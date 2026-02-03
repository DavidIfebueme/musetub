from datetime import datetime, timedelta, timezone
import secrets
from uuid import uuid4

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
from app.platform.db.models import Content, PaymentChannel, Settlement, StreamCredit, User
from app.platform.db.session import get_session
from app.platform.security import get_current_user
from app.platform.services.chain import ChainClient
from app.platform.services.circle_wallets import CircleWalletsClient
from app.platform.services.gemini import get_or_create_pricing_explanation
from app.platform.services.ipfs import IPFSClient
from app.platform.services.x402 import (
    build_402_body,
    build_exact_accept,
    encode_payment_response,
)

router = APIRouter(prefix="/content")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_X402_CHUNK_SECONDS = 10
_ARC_TESTNET_USDC_ADDRESS = "0x3600000000000000000000000000000000000000"

_SUPPORTED_CACHE: dict | None = None
_SUPPORTED_CACHE_EXPIRES_AT: float = 0.0
_SUPPORTED_TTL_SECONDS = 300.0


def get_ipfs_client() -> IPFSClient:
    return IPFSClient()


def _forbidden() -> HTTPException:
    return HTTPException(status_code=403, detail="Forbidden")


def _service_unavailable(message: str) -> HTTPException:
    return HTTPException(status_code=503, detail=message)


def get_circle_wallets_client() -> CircleWalletsClient:
    return CircleWalletsClient()


def _live_stream_pay_enabled() -> bool:
    return bool(
        settings.circle_api_key
        and settings.circle_entity_secret
        and settings.arc_rpc_url
        and settings.arc_chain_id is not None
        and settings.usdc_address
        and settings.escrow_address
    )


async def _get_or_create_channel(
    *,
    session: AsyncSession,
    user_id: str,
    content: Content,
) -> PaymentChannel:
    channel_result = await session.execute(
        select(PaymentChannel)
        .where(
            PaymentChannel.user_id == user_id,
            PaymentChannel.content_id == content.id,
            PaymentChannel.status == "active",
        )
        .order_by(PaymentChannel.opened_at.desc())
        .limit(1)
    )
    channel = channel_result.scalar_one_or_none()
    if channel is None:
        channel = PaymentChannel(
            user_id=user_id,
            content_id=content.id,
            price_per_second_locked=content.price_per_second,
            status="active",
        )
        session.add(channel)
        await session.flush()
    return channel


async def _get_or_create_credit(
    *,
    session: AsyncSession,
    user_id: str,
    content_id: str,
) -> StreamCredit:
    credit_result = await session.execute(
        select(StreamCredit)
        .where(StreamCredit.user_id == user_id, StreamCredit.content_id == content_id)
        .with_for_update()
    )
    credit = credit_result.scalar_one_or_none()
    if credit is None:
        credit = StreamCredit(user_id=user_id, content_id=content_id, seconds_remaining=0)
        session.add(credit)
        await session.flush()
    return credit


async def _get_gateway_supported_kinds(*, sidecar_url: str) -> dict | None:
    global _SUPPORTED_CACHE, _SUPPORTED_CACHE_EXPIRES_AT
    now = datetime.now(timezone.utc).timestamp()
    if _SUPPORTED_CACHE and _SUPPORTED_CACHE_EXPIRES_AT > now:
        return _SUPPORTED_CACHE

    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(f"{sidecar_url.rstrip('/')}/supported")
            resp.raise_for_status()
            data = resp.json()
        except httpx.RequestError:
            return None
        except httpx.HTTPStatusError:
            return None

    if isinstance(data, dict):
        _SUPPORTED_CACHE = data
        _SUPPORTED_CACHE_EXPIRES_AT = now + _SUPPORTED_TTL_SECONDS
        return data
    return None


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
        try:
            resp = await client.post(
                f"{sidecar_url.rstrip('/')}/pay",
                json={"contentId": content_id, "accessToken": access_token},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as exc:
            raise _service_unavailable(f"x402 gateway sidecar unreachable at {sidecar_url}") from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail="x402 gateway sidecar error") from exc


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

    kind_extra: dict | None = None
    if settings.x402_gateway_sidecar_url:
        supported = await _get_gateway_supported_kinds(sidecar_url=settings.x402_gateway_sidecar_url)
        if isinstance(supported, dict):
            kinds = supported.get("kinds")
            if isinstance(kinds, list):
                for kind in kinds:
                    if not isinstance(kind, dict):
                        continue
                    if kind.get("scheme") != "exact":
                        continue
                    if kind.get("network") != settings.x402_network:
                        continue
                    extra = kind.get("extra")
                    if isinstance(extra, dict):
                        kind_extra = extra
                        break

    accepts = [
        build_exact_accept(
            network=settings.x402_network,
            asset=asset,
            amount=amount,
            pay_to=seller_address,
            max_timeout_seconds=settings.x402_max_timeout_seconds,
            extra=kind_extra or {"name": settings.usdc_name, "version": settings.usdc_version},
        )
    ]

    credit = await _get_or_create_credit(session=session, user_id=user.id, content_id=row.id)
    if int(credit.seconds_remaining) < _X402_CHUNK_SECONDS:
        body = build_402_body(
            url=str(request.url),
            description=f"Stream {row.title} ({_X402_CHUNK_SECONDS}s)",
            mime_type="application/json",
            accepts=accepts,
        )
        return JSONResponse(status_code=402, content=body)

    credit.seconds_remaining = int(credit.seconds_remaining) - _X402_CHUNK_SECONDS

    channel = await _get_or_create_channel(session=session, user_id=user.id, content=row)
    now = _utcnow()
    channel.total_seconds_streamed = int(channel.total_seconds_streamed) + _X402_CHUNK_SECONDS
    channel.total_amount_owed = int(channel.total_amount_owed) + amount
    channel.last_tick_at = now

    await session.commit()
    return StreamResponse(
        playback_url=ipfs.playback_url(row.ipfs_cid),
        seconds_remaining=int(credit.seconds_remaining),
    )


@router.post("/{content_id}/pay", response_model=StreamResponse)
async def pay_stream_content(
    content_id: str,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    ipfs: IPFSClient = Depends(get_ipfs_client),
    circle: CircleWalletsClient = Depends(get_circle_wallets_client),
) -> StreamResponse:
    user = await _require_user_for_stream(request, session)

    result = await session.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Not found")

    creator_result = await session.execute(select(User).where(User.id == content.creator_id))
    creator = creator_result.scalar_one_or_none()
    if creator is None:
        raise HTTPException(status_code=404, detail="Creator not found")

    if not creator.wallet_address:
        raise HTTPException(status_code=400, detail="Creator wallet not available")

    amount = int(content.price_per_second) * _X402_CHUNK_SECONDS
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid price")

    tx_id: str
    payer: str

    if _live_stream_pay_enabled():
        if not user.circle_wallet_id or not user.wallet_address:
            raise HTTPException(status_code=400, detail="User wallet not available")

        chain = ChainClient.from_settings()

        nonce = "0x" + secrets.token_hex(32)
        now = _utcnow()
        valid_after = int(now.timestamp()) - 5
        valid_before = int((now + timedelta(minutes=5)).timestamp())

        typed_data = chain.erc3009_receive_with_authorization_typed_data(
            from_address=user.wallet_address,
            to_address=chain.config.escrow_address,
            value=amount,
            valid_after=valid_after,
            valid_before=valid_before,
            nonce=nonce,
        )

        signature = await circle.sign_typed_data(
            wallet_id=user.circle_wallet_id,
            blockchain=settings.circle_blockchain,
            typed_data=typed_data,
            memo=f"musetub:prepay:{content.id}",
        )

        tx_id = await circle.create_contract_execution_transaction(
            wallet_id=user.circle_wallet_id,
            blockchain=settings.circle_blockchain,
            contract_address=chain.config.escrow_address,
            abi_function_signature="streamWithAuthorization(address,address,uint256,uint256,uint256,bytes32,bytes)",
            abi_parameters=[
                user.wallet_address,
                creator.wallet_address,
                amount,
                valid_after,
                valid_before,
                nonce,
                signature,
            ],
            ref_id=f"prepay:{user.id}:{content.id}",
        )

        payer = user.wallet_address
    else:
        tx_id = f"simulated:{uuid4()}"
        payer = user.wallet_address or "unknown"

    channel = await _get_or_create_channel(session=session, user_id=user.id, content=content)
    session.add(Settlement(channel_id=channel.id, amount=amount, tx_hash=tx_id))
    channel.total_amount_settled = int(channel.total_amount_settled) + amount
    channel.last_settlement_at = _utcnow()

    credit = await _get_or_create_credit(session=session, user_id=user.id, content_id=content.id)
    credit.seconds_remaining = int(credit.seconds_remaining) + _X402_CHUNK_SECONDS

    await session.commit()

    response.headers["Payment-Response"] = encode_payment_response({"transaction": tx_id, "payer": payer})
    return StreamResponse(
        playback_url=ipfs.playback_url(content.ipfs_cid),
        seconds_remaining=int(credit.seconds_remaining),
    )
