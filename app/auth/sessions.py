from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.config import settings

COOKIE_NAME = "session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7 * 12  # 12 weeks in seconds

_serializer = URLSafeTimedSerializer(settings.session_secret)


def encode_session(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def decode_session(token: str) -> int | None:
    try:
        data = _serializer.loads(token, max_age=COOKIE_MAX_AGE)
        return data["user_id"]
    except (BadSignature, SignatureExpired, KeyError):
        return None
