from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_agents.services.pricing import compute_suggested_price_per_second_minor_units
from app.features.ai_agents.services.quality import compute_quality_score
from app.features.content.schemas import ContentListItem, ContentResponse, StreamResponse
from app.platform.config import settings
from app.platform.db.models import Content, PaymentChannel, Settlement, User
from app.platform.db.session import get_session
from app.platform.security import get_current_user
from app.platform.services.gemini import get_or_create_pricing_explanation
from app.platform.services.ipfs import IPFSClient
from app.platform.services.x402 import (
    build_402_body,
    build_exact_accept,
    decode_payment_signature,
    encode_payment_response,
    verify_and_settle_simulated,
    verify_and_settle_via_sidecar,
)

router = APIRouter(prefix="/content")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_X402_CHUNK_SECONDS = 10
_ARC_TESTNET_USDC_ADDRESS = "0x3600000000000000000000000000000000000000"


def get_ipfs_client() -> IPFSClient:
    return IPFSClient()


def _forbidden() -> HTTPException:
    return HTTPException(status_code=403, detail="Forbidden")


def _service_unavailable(message: str) -> HTTPException:
    return HTTPException(status_code=503, detail=message)


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Unauthorized")


async def _require_user_for_stream(request: Request, session: AsyncSession):
    header = request.headers.get("authorization")
    token: str | None = None
    if header and header.lower().startswith("bearer "):
        token = header.split(" ", 1)[1].strip()
    else:
        token = request.query_params.get("access_token")

    if not token:
        raise _unauthorized()

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise _unauthorized() from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise _unauthorized()

    result = await session.execute(select(User).where(User.id == subject))
    user = result.scalar_one_or_none()
    if user is None:
        raise _unauthorized()

    return user


def _extract_access_token(request: Request) -> str:
    header = request.headers.get("authorization")
    if header and header.lower().startswith("bearer "):
        token = header.split(" ", 1)[1].strip()
        if token:
            return token
    token = request.query_params.get("access_token")
    if token:
        return token
    raise _unauthorized()


async def _pay_via_sidecar(*, sidecar_url: str, content_id: str, access_token: str) -> dict:
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{sidecar_url.rstrip('/')}/pay",
            json={"contentId": content_id, "accessToken": access_token},
        )
        resp.raise_for_status()
        return resp.json()


@router.post("/upload", response_model=ContentResponse)
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...),
    content_type: str = Form(...),
    duration_seconds: int = Form(...),
    resolution: str = Form(...),
    bitrate_tier: str = Form(...),
    engagement_intent: str = Form(...),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    ipfs: IPFSClient = Depends(get_ipfs_client),
) -> ContentResponse:
    if not getattr(user, "is_creator", False):
        raise _forbidden()

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    cid = await ipfs.add_bytes(file_bytes, filename=file.filename or "upload")

    quality_score = compute_quality_score(
        duration_seconds=duration_seconds,
        resolution=resolution,
        bitrate_tier=bitrate_tier,
        content_type=content_type,
        engagement_intent=engagement_intent,
    )
    suggested = compute_suggested_price_per_second_minor_units(quality_score=quality_score)

    metadata = {
        "title": title,
        "description": description,
        "content_type": content_type,
        "duration_seconds": duration_seconds,
        "resolution": resolution,
        "bitrate_tier": bitrate_tier,
        "engagement_intent": engagement_intent,
    }

    explanation = await get_or_create_pricing_explanation(
        session=session,
        metadata=metadata,
        suggested_price_per_second=suggested,
        quality_score=quality_score,
    )

    row = Content(
        creator_id=user.id,
        title=title,
        description=description,
        content_type=content_type,
        duration_seconds=duration_seconds,
        resolution=resolution,
        bitrate_tier=bitrate_tier,
        engagement_intent=engagement_intent,
        quality_score=quality_score,
        suggested_price_per_second=suggested,
        price_per_second=suggested,
        ipfs_cid=cid,
    )

    session.add(row)
    await session.commit()
    await session.refresh(row)

    return ContentResponse(
        id=row.id,
        creator_id=row.creator_id,
        title=row.title,
        description=row.description,
        content_type=row.content_type,
        duration_seconds=row.duration_seconds,
        resolution=row.resolution,
        bitrate_tier=row.bitrate_tier,
        engagement_intent=row.engagement_intent,
        quality_score=row.quality_score,
        suggested_price_per_second=row.suggested_price_per_second,
        price_per_second=row.price_per_second,
        ipfs_cid=row.ipfs_cid,
        playback_url=ipfs.playback_url(row.ipfs_cid),
        pricing_explanation=explanation,
        created_at=row.created_at,
    )


@router.get("", response_model=list[ContentListItem])
async def list_content(
    session: AsyncSession = Depends(get_session),
    ipfs: IPFSClient = Depends(get_ipfs_client),
) -> list[ContentListItem]:
    result = await session.execute(select(Content).order_by(Content.created_at.desc()).limit(100))
    rows = list(result.scalars().all())

    return [
        ContentListItem(
            id=row.id,
            creator_id=row.creator_id,
            title=row.title,
            content_type=row.content_type,
            duration_seconds=row.duration_seconds,
            price_per_second=row.price_per_second,
            quality_score=row.quality_score,
            playback_url=ipfs.playback_url(row.ipfs_cid),
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    session: AsyncSession = Depends(get_session),
    ipfs: IPFSClient = Depends(get_ipfs_client),
) -> ContentResponse:
    result = await session.execute(select(Content).where(Content.id == content_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")

    metadata = {
        "title": row.title,
        "description": row.description,
        "content_type": row.content_type,
        "duration_seconds": row.duration_seconds,
        "resolution": row.resolution,
        "bitrate_tier": row.bitrate_tier,
        "engagement_intent": row.engagement_intent,
    }

    explanation = await get_or_create_pricing_explanation(
        session=session,
        metadata=metadata,
        suggested_price_per_second=row.suggested_price_per_second,
        quality_score=row.quality_score,
    )

    return ContentResponse(
        id=row.id,
        creator_id=row.creator_id,
        title=row.title,
        description=row.description,
        content_type=row.content_type,
        duration_seconds=row.duration_seconds,
        resolution=row.resolution,
        bitrate_tier=row.bitrate_tier,
        engagement_intent=row.engagement_intent,
        quality_score=row.quality_score,
        suggested_price_per_second=row.suggested_price_per_second,
        price_per_second=row.price_per_second,
        ipfs_cid=row.ipfs_cid,
        playback_url=ipfs.playback_url(row.ipfs_cid),
        pricing_explanation=explanation,
        created_at=row.created_at,
    )


@router.get("/{content_id}/stream", response_model=StreamResponse)
async def stream_content(
    content_id: str,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    ipfs: IPFSClient = Depends(get_ipfs_client),
) -> StreamResponse:
    user = await _require_user_for_stream(request, session)
    result = await session.execute(select(Content).where(Content.id == content_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")

    creator_result = await session.execute(select(User).where(User.id == row.creator_id))
    creator = creator_result.scalar_one_or_none()
    seller_address = getattr(creator, "wallet_address", None) or settings.x402_default_seller_address
    if not seller_address:
        raise _service_unavailable("Seller address not configured")

    asset = settings.usdc_address or _ARC_TESTNET_USDC_ADDRESS
    amount = int(row.price_per_second) * _X402_CHUNK_SECONDS
    accepts = [
        build_exact_accept(
            network=settings.x402_network,
            asset=asset,
            amount=amount,
            pay_to=seller_address,
            max_timeout_seconds=settings.x402_max_timeout_seconds,
            extra={"name": settings.usdc_name, "version": settings.usdc_version},
        )
    ]

    payment_header = request.headers.get("payment-signature")
    if not payment_header:
        body = build_402_body(
            url=str(request.url),
            description=f"Stream {row.title} ({_X402_CHUNK_SECONDS}s)",
            mime_type="application/json",
            accepts=accepts,
        )
        return JSONResponse(status_code=402, content=body)

    try:
        payment_payload = decode_payment_signature(payment_header)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    accepted = payment_payload.get("accepted")
    if not isinstance(accepted, dict):
        raise HTTPException(status_code=400, detail="Missing accepted requirements")

    if accepted.get("amount") != str(amount):
        raise HTTPException(status_code=400, detail="Accepted amount mismatch")

    if accepted.get("payTo") != seller_address:
        raise HTTPException(status_code=400, detail="Accepted payTo mismatch")

    if accepted.get("network") != settings.x402_network:
        raise HTTPException(status_code=400, detail="Accepted network mismatch")

    if accepted.get("asset") != asset:
        raise HTTPException(status_code=400, detail="Accepted asset mismatch")

    if settings.x402_gateway_sidecar_url:
        settlement = await verify_and_settle_via_sidecar(
            sidecar_url=settings.x402_gateway_sidecar_url,
            payment_payload=payment_payload,
            requirements=accepted,
        )
    else:
        settlement = await verify_and_settle_simulated(payment_payload=payment_payload)

    response.headers["Payment-Response"] = encode_payment_response(
        {"transaction": settlement.transaction, "payer": settlement.payer}
    )

    channel_result = await session.execute(
        select(PaymentChannel)
        .where(
            PaymentChannel.user_id == user.id,
            PaymentChannel.content_id == row.id,
            PaymentChannel.status == "active",
        )
        .order_by(PaymentChannel.opened_at.desc())
        .limit(1)
    )
    channel = channel_result.scalar_one_or_none()
    if channel is None:
        channel = PaymentChannel(
            user_id=user.id,
            content_id=row.id,
            price_per_second_locked=row.price_per_second,
            status="active",
        )
        session.add(channel)
        await session.flush()

    now = _utcnow()
    channel.total_seconds_streamed = int(channel.total_seconds_streamed) + _X402_CHUNK_SECONDS
    channel.total_amount_owed = int(channel.total_amount_owed) + amount
    channel.total_amount_settled = int(channel.total_amount_settled) + amount
    channel.last_tick_at = now
    channel.last_settlement_at = now

    session.add(
        Settlement(
            channel_id=channel.id,
            amount=amount,
            tx_hash=settlement.transaction,
        )
    )
    await session.commit()

    return StreamResponse(playback_url=ipfs.playback_url(row.ipfs_cid))


@router.post("/{content_id}/pay", response_model=StreamResponse)
async def pay_stream_content(
    content_id: str,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> StreamResponse:
    await _require_user_for_stream(request, session)
    access_token = _extract_access_token(request)

    if not settings.x402_gateway_sidecar_url:
        raise _service_unavailable("x402 gateway sidecar not configured")

    data = await _pay_via_sidecar(
        sidecar_url=settings.x402_gateway_sidecar_url,
        content_id=content_id,
        access_token=access_token,
    )

    playback_url = data.get("playback_url")
    if isinstance(data.get("transaction"), str) and data["transaction"]:
        response.headers["Payment-Response"] = encode_payment_response(
            {"transaction": data["transaction"], "payer": data.get("payer") or "unknown"}
        )

    if not isinstance(playback_url, str) or not playback_url:
        raise HTTPException(status_code=502, detail="Invalid sidecar response")
    return StreamResponse(playback_url=playback_url)
