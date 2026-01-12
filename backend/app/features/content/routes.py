from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_agents.services.pricing import compute_suggested_price_per_second_minor_units
from app.features.ai_agents.services.quality import compute_quality_score
from app.features.content.schemas import ContentListItem, ContentResponse
from app.platform.db.models import Content
from app.platform.db.session import get_session
from app.platform.security import get_current_user
from app.platform.services.gemini import get_or_create_pricing_explanation
from app.platform.services.ipfs import IPFSClient

router = APIRouter(prefix="/content")


def get_ipfs_client() -> IPFSClient:
    return IPFSClient()


def _forbidden() -> HTTPException:
    return HTTPException(status_code=403, detail="Forbidden")


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
