import logging
import traceback
from typing import Any, Optional
from urllib.error import URLError

from cloudscraper.exceptions import AbortedException, CloudflareException
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from PIL import UnidentifiedImageError
from requests.exceptions import RequestException
from urllib3.exceptions import HTTPError

__all__ = [
    "LNException",
    "ServerError",
    "ServerErrors",
    "AbortedException",
    "RetryErrorGroup",
    "ScraperErrorGroup",
    "FallbackToBrowser",
    "attach_exception_handlers",
]


class LNException(Exception):
    pass


class FallbackToBrowser(Exception):
    pass


ScraperErrorGroup = (
    URLError,
    HTTPError,
    CloudflareException,
    RequestException,
    FallbackToBrowser,
    UnidentifiedImageError,
)

RetryErrorGroup = (
    URLError,
    HTTPError,
    CloudflareException,
    RequestException,
    UnidentifiedImageError,
)


class ServerError(HTTPException, LNException):
    def __init__(self, status=400, *args, **kwargs) -> None:
        self.extra: Optional[str] = None
        super().__init__(status, *args, **kwargs)

    def with_extra(self, extra: Any) -> "ServerError":
        self.extra = str(extra).strip()
        return self

    def __str__(self) -> str:
        error = f"Error({self.status_code}): {self.detail}"
        if self.extra:
            error += f" [{self.extra}]"
        return error

    def format(self, with_stack=False) -> str:
        stack = ""
        if with_stack:
            lines = traceback.format_exception(
                type(self),
                self,
                self.__traceback__,
                chain=True,
            )
            stack = "".join(lines)
        return f"{self}\n{stack}".strip()

    def to_response(self):
        return JSONResponse(
            status_code=self.status_code,
            headers=self.headers,
            content={
                "error": self.detail,
                "detail": self.extra,
            },
        )


def attach_exception_handlers(app: FastAPI):
    def server_error_handler(req: Request, err: ServerError):
        return err.to_response()

    def http_exception_handler(req: Request, err: HTTPException):
        logging.error(repr(err), exc_info=True)
        return JSONResponse(
            status_code=err.status_code,
            content={"error": err.detail},
            headers=err.headers,
        )

    def general_exception_handler(req: Request, err: Exception):
        logging.error(repr(err), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error"},
        )

    app.exception_handler(ServerError)(server_error_handler)
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(Exception)(general_exception_handler)


class ServerErrors:
    forbidden = ServerError(403, "Forbidden")
    not_found = ServerError(404, "Not Found")
    unauthorized = ServerError(401, "Unauthorized")
    server_error = ServerError(500, "Internal Server Error")

    wrong_otp = ServerError(403, "Wrong OTP")
    token_invalid = ServerError(403, "Invalid token")
    token_expired = ServerError(403, "Token expired")
    inactive_user = ServerError(403, "User is inactive")
    user_exists = ServerError(409, "User already exists")
    email_not_verified = ServerError(401, "Email is not verified")
    email_already_verified = ServerError(409, "Email is already verified")
    can_not_delete_self = ServerError(403, "You are not allowed to delete your own account")

    invalid_url = ServerError(422, "Invalid URL")
    invalid_input = ServerError(422, "Invalid input")
    no_chapters_to_download = ServerError(422, "No chapters to download")
    no_volumes_to_download = ServerError(422, "No volumes to download")
    no_images_to_download = ServerError(422, "No images to download")
    no_artifacts_to_create = ServerError(422, "No artifacts to create")
    sort_column_is_none = ServerError(422, "No such field to sort by")
    duplicate_output_format = ServerError(422, "Duplicate formats are not allowed")

    no_such_user = ServerError(404, "No such user")
    no_such_job = ServerError(404, "No such job")
    no_such_file = ServerError(404, "No such file")
    no_such_novel = ServerError(404, "No such novel")
    no_such_tag = ServerError(404, "No such tag")
    no_such_library = ServerError(404, "No such library")
    no_such_secret = ServerError(404, "No such secret")
    no_such_volume = ServerError(404, "No such volume")
    no_such_chapter = ServerError(404, "No such chapter")
    no_such_artifact = ServerError(404, "No such artifact")
    no_artifact_file = ServerError(404, "Artifact file not available")

    no_novel_title = ServerError(500, "Novel has no title")
    no_chapters = ServerError(500, "No chapters found")
    no_volumes = ServerError(500, "No volumes found")
    no_images = ServerError(500, "No images found")
    unable_to_resume_job = ServerError(500, "Unable to resume Job")
    no_novel_cover = ServerError(500, "Novel cover is not available")
    invalid_image_response = ServerError(500, "Invalid image response")
    smtp_server_unavailable = ServerError(500, "SMTP server is not available")
    smtp_server_login_fail = ServerError(500, "Failed to login to SMTP server")
    email_send_failure = ServerError(500, "Failed to send email")
    calibre_exe_not_found = ServerError(500, "No calibre executables")
    no_epub_file = ServerError(500, "No EPub file found")
    acquire_lock = ServerError(500, "Failed to acquire lock")
    ebook_convert_error = ServerError(500, "Failed running ebook-convert")
    failed_creating_artifact = ServerError(500, "Failed to create artifact")
    format_not_available = ServerError(500, "The output format is not available")
    host_rejected = ServerError(500, "The requested domain is rejected")
    source_not_loaded = ServerError(500, "Sources are not loaded")
    no_crawler = ServerError(500, "No crawler found for the domain")
