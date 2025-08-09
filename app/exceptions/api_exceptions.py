from fastapi import HTTPException


class APIException(HTTPException):
    """Base HTTP exception class for the application."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(status_code=status_code, detail=message)


class DeveloperException(APIException):
    def __init__(self, message: str, status_code: int):
        super().__init__(message, status_code)


class DatabaseConnectionException(APIException):
    def __init__(self, message: str = "Database connection error"):
        super().__init__(message, 503)


class IntegrityConstraintException(APIException):
    def __init__(self, message: str = "Data integrity constraint violation"):
        super().__init__(message, 409)


class NotFoundException(APIException):
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", 404)


class AlreadyExistsException(APIException):
    def __init__(self, resource: str):
        super().__init__(f"{resource} already exists", 409)
