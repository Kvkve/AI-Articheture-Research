# The sign-in endpoint. It needs no token, so it is not on the router of
# app/protected.py.
# Follows login_access_token in backend/app/api/routes/login.py of the
# official FastAPI full-stack template (MIT license). See docs/sources.md.
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from app.dependencies import ConnectionDependency, ErrorMessage, SettingsDependency
from app.security import create_access_token
from app.users import authenticate

router = APIRouter(tags=["sign-in"])


class Token(BaseModel):
    access_token: str = Field(description="The signed token.")
    token_type: str = Field(
        default="bearer",
        description="Send the token in the header Authorization: Bearer <token>.",
    )


@router.post(
    "/login/access-token",
    summary="Sign in with a user name and a password, and get a token",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorMessage,
            "description": "The user name or the password is wrong",
        },
    },
)
def login_access_token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: SettingsDependency,
    connection: ConnectionDependency,
) -> Token:
    user = authenticate(connection, form.username, form.password)
    if user is None:
        # The same answer for an unknown name and a wrong password, so the
        # answer does not tell which user names exist.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect user name or password",
        )
    token = create_access_token(
        user.id,
        settings.token_secret_key.get_secret_value(),
        timedelta(minutes=settings.token_expire_minutes),
    )
    return Token(access_token=token)
