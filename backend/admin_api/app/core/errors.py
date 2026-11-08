class AdminAPIError(Exception):
    status_code = 500
    detail = "An unexpected admin API error occurred"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class ResourceNotFoundError(AdminAPIError):
    status_code = 404


class ResourceValidationError(AdminAPIError):
    status_code = 422


class ResourceConflictError(AdminAPIError):
    status_code = 409
    detail = "The request conflicts with an existing resource or database constraint"
