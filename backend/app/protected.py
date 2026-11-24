# Every endpoint that needs a token goes on this router. The router asks for
# the signed-in user before any of its endpoints runs, so an endpoint added
# here cannot forget the token.
from fastapi import APIRouter, Depends, status

from app.dependencies import CurrentUser, ErrorMessage, get_current_user
from app.users import User

router = APIRouter(
    dependencies=[Depends(get_current_user)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorMessage,
            "description": "No token, or the token is not valid. Sign in again.",
        },
    },
)


@router.get(
    "/users/me",
    tags=["users"],
    summary="Get the signed-in user",
)
def read_current_user(user: CurrentUser) -> User:
    # FastAPI runs get_current_user once per request, even though both the
    # router and this endpoint ask for it.
    return user
