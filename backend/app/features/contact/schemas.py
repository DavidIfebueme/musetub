from pydantic import BaseModel, EmailStr, Field


class ContactMessageRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    message: str = Field(min_length=1, max_length=4000)


class CreatorAccessRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    channel_link: str | None = Field(default=None, max_length=500)
    message: str | None = Field(default=None, max_length=4000)


class ContactResponse(BaseModel):
    status: str
