from fastapi import HTTPException, status


class AuthException(HTTPException):
    """Базовый класс для исключений аутентификации"""
    pass


class InvalidCredentials(AuthException):
    """Неверные учетные данные"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


class InactiveUser(AuthException):
    """Пользователь неактивен"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive"
        )


class EmailAlreadyRegistered(AuthException):
    """Email уже зарегистрирован"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )


class MissingAccessToken(AuthException):
    """Отсутствует access token"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token"
        )


class InvalidAccessToken(AuthException):
    """Неверный access token"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )


class AccessTokenExpired(AuthException):
    """Access token истек"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired"
        )


class MissingRefreshToken(AuthException):
    """Отсутствует refresh token"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token"
        )


class InvalidRefreshToken(AuthException):
    """Неверный или истекший refresh token"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


class RefreshTokenExpired(AuthException):
    """Refresh token истек"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )


class UserNotFound(AuthException):
    """Пользователь не найден"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


class ProfileNotFound(AuthException):
    """Профиль не найден"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )


class InvalidTokenPayload(AuthException):
    """Неверная структура токена"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )


class TokenExpired(AuthException):
    """Токен истек"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )


class InvalidToken(AuthException):
    """Неверный токен"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
