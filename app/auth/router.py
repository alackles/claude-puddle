from fastapi import APIRouter, Depends, HTTPException, Response, Request
import aiosqlite
from app.db.connection import get_db
from app.db.queries import get_user_by_email, create_user, get_invite_code, update_user_password
from app.auth.passwords import hash_password, verify_password
from app.auth.sessions import encode_session, COOKIE_NAME, COOKIE_MAX_AGE
from app.auth.dependencies import get_current_user
from app.models.schemas import RegisterRequest, LoginRequest, ChangePasswordRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(
    body: RegisterRequest,
    response: Response,
    db: aiosqlite.Connection = Depends(get_db),
):
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    invite = await get_invite_code(db, body.invite_code)
    if invite is None:
        raise HTTPException(status_code=400, detail="Invalid or inactive invite code")

    password_hash = hash_password(body.password)
    user_id = await create_user(
        db,
        email=body.email,
        password_hash=password_hash,
        display_name=body.display_name,
        invite_code_id=invite["id"],
    )

    token = encode_session(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return {"message": "Registered successfully"}


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    db: aiosqlite.Connection = Depends(get_db),
):
    user = await get_user_by_email(db, body.email)
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = encode_session(user["id"])
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return UserResponse(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        is_instructor=bool(user["is_instructor"]),
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Logged out"}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    if not verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_hash = hash_password(body.new_password)
    await update_user_password(db, user["id"], new_hash)
    return {"message": "Password updated"}


@router.get("/me", response_model=UserResponse)
async def me(user: aiosqlite.Row = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        is_instructor=bool(user["is_instructor"]),
    )
