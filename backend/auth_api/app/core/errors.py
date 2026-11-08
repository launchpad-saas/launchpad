class AuthAPIError(Exception):
    status_code = 500
    detail = "An unexpected authentication error occurred"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class AuthNotFoundError(AuthAPIError):
    status_code = 404


class AuthConflictError(AuthAPIError):
    status_code = 409


class AuthValidationError(AuthAPIError):
    status_code = 400


class AuthUnavailableError(AuthAPIError):
    status_code = 503


class InvalidCredentialsError(AuthAPIError):
    status_code = 401
    detail = "Invalid email or password"


class RateLimitError(AuthAPIError):
    status_code = 429
