from pydantic import BaseModel, field_validator
from typing import Optional


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str
    invite_code: str

    @field_validator("email")
    @classmethod
    def must_be_lawrence_email(cls, v: str) -> str:
        if not v.lower().endswith("@lawrence.edu"):
            raise ValueError("Registration requires a @lawrence.edu email address")
        return v.lower()


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ConversationCreateRequest(BaseModel):
    title: str


class MessageRequest(BaseModel):
    content: str
    attachment_filename: Optional[str] = None
    attachment_content: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    is_instructor: bool


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    shared_with_instructor: bool
    owner_email: Optional[str] = None
    owner_display_name: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    attachment_filename: Optional[str]
    created_at: str
