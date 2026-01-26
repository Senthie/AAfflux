"""
Author: Senthie seemoon2077@gmail.com
Date: 2026-01-05 15:02:39
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-26 12:11:53
FilePath: /api/app/core/exceptions.py
Description: Custom exceptions for the application.

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from app.enums.custom_response_code_enum import CustomResponseCodeEnum


class AuthException(Exception):
    """Business logic exception with custom response code."""

    def __init__(self, response_code: CustomResponseCodeEnum, message: str | None = None):
        self.response_code = response_code
        self.message = message or response_code.msg
        super().__init__(self.message)


class EmailAlreadyExistsException(AuthException):
    """Exception raised when email already exists."""

    def __init__(self):
        super().__init__(CustomResponseCodeEnum.EMAIL_ALREADY_EXISTS)


class InvalidCredentialsException(AuthException):
    """Exception raised when credentials are invalid."""

    def __init__(self):
        super().__init__(CustomResponseCodeEnum.UNAUTHORIZED, 'Invalid email or password')


class PasswordValidationException(AuthException):
    """Exception raised when password validation fails."""

    def __init__(self, response_code: CustomResponseCodeEnum):
        super().__init__(response_code)


## -------------------- Workspace --------------------------------- ##


class WorkspaceException(Exception):
    """Business logic exception with custom response code."""

    def __init__(self, response_code: CustomResponseCodeEnum, message: str | None = None):
        self.response_code = response_code
        self.message = message or response_code.msg
        super().__init__(self.message)


class WorkflowError(Exception):
    """Exception raised when workflow is not found."""

    def __init__(self, response_code: CustomResponseCodeEnum, message: str | None = None):
        self.response_code = response_code
        self.message = message or response_code.msg
        super().__init__(self.message)
