from datetime import datetime, timedelta, timezone
import jwt
import logging
from src.config import settings
import bcrypt
from src.auth.exceptions import TokenExpired, InvalidToken

logger = logging.getLogger(__name__)


def encode_jwt(
    payload: dict,
    private_key: str = None,
    algorithm: str = None,
) -> str:
    if private_key is None:
        private_key = settings.auth_jwt.private_key
    if algorithm is None:
        algorithm = settings.auth_jwt.algorithm or "RS256"
    
    return jwt.encode(payload, private_key, algorithm=algorithm)


def decode_jwt(
    token: str | bytes,
    public_key: str = None,
    algorithm: str = None
) -> dict:
    if public_key is None:
        public_key = settings.auth_jwt.public_key
    if algorithm is None:
        algorithm = settings.auth_jwt.algorithm or "RS256"
    
    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=[algorithm],
            options={"verify_exp": True}
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise TokenExpired()
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise InvalidToken()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(
    data: dict,
    expires_delta: int = settings.auth_jwt.access_token_expires_minutes
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return encode_jwt(to_encode)


def create_refresh_token(
    data: dict,
    expires_delta: int = settings.auth_jwt.refresh_token_expires_days
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=expires_delta)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return encode_jwt(to_encode)


def get_token_expiration(token: str) -> datetime:
    decoded = decode_jwt(token)
    exp_timestamp = decoded.get("exp")
    if exp_timestamp is None:
        raise ValueError("Token does not contain 'exp' claim")
    return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)


def is_token_expired(token: str) -> bool:
    return datetime.now(timezone.utc) > get_token_expiration(token)
