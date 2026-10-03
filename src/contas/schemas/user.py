from pydantic import BaseModel, EmailStr, Field


class RegisterUserInput(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=6)


class AuthenticateUserInput(BaseModel):
    identifier: str = Field(min_length=1)  # username or email
    password: str = Field(min_length=1)


class GoogleAuthInput(BaseModel):
    google_id: str
    email: EmailStr
    name: str
    avatar_url: str | None = None


class ApproveUserInput(BaseModel):
    user_id: str
    approve: bool = True


class ChangePasswordInput(BaseModel):
    user_id: str
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6)


class AdminResetPasswordInput(BaseModel):
    target_user_id: str
    new_password: str = Field(min_length=6)
