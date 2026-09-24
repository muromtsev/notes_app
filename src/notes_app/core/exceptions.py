class AppError(Exception):
    """Базовое доменное исключение"""

    status_code: int = 400
    code: str = "arr_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EmailAlreadyExistsError(AppError):
    status_code = 409
    code = "email_already_exists"


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "invalid_credentials"


class InvalidTokenError(AppError):
    status_code = 401
    code = "invalid_code"


class UserNotFoundError(AppError):
    status_code = 404
    code = "user_not_found"

