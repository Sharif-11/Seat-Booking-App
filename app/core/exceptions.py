from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}

    for err in exc.errors():
        field = err["loc"][-1]
        message = err["msg"]

        errors[field] = message

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "status_code": 422,
            "message": "Validation failed",
            "errors": errors
        }
    )