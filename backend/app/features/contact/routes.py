from fastapi import APIRouter, HTTPException

from app.features.contact.schemas import ContactMessageRequest, CreatorAccessRequest, ContactResponse
from app.features.contact.services import EmailServiceError, send_contact_email

router = APIRouter(prefix="/contact")


def _service_unavailable(detail: str) -> HTTPException:
    return HTTPException(status_code=503, detail=detail)


@router.post("/message", response_model=ContactResponse)
async def contact_message(body: ContactMessageRequest) -> ContactResponse:
    subject = f"MuseTub contact from {body.name}"
    message = f"From: {body.name}\nEmail: {body.email}\n\n{body.message}"
    try:
        await send_contact_email(subject=subject, body=message, reply_to=body.email)
    except EmailServiceError as exc:
        raise _service_unavailable(str(exc)) from exc

    return ContactResponse(status="sent")


@router.post("/creator-access", response_model=ContactResponse)
async def creator_access(body: CreatorAccessRequest) -> ContactResponse:
    subject = f"MuseTub creator access request from {body.name}"
    lines = [f"From: {body.name}", f"Email: {body.email}"]
    if body.channel_link:
        lines.append(f"Channel: {body.channel_link}")
    if body.message:
        lines.append("")
        lines.append(body.message)
    message = "\n".join(lines)

    try:
        await send_contact_email(subject=subject, body=message, reply_to=body.email)
    except EmailServiceError as exc:
        raise _service_unavailable(str(exc)) from exc

    return ContactResponse(status="sent")
