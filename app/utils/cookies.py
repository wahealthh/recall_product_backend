from typing import Dict, Optional
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi import Request, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED


class OAuth2PasswordBearerWithCookie(OAuth2):
    """
    A subclass of `OAuth2` that adds support for cookie-based token authentication.

    This class is designed to work with FastAPI's `OAuth2` authentication scheme,
    but with the added ability to parse tokens from the `access_token` cookie.

    Parameters:
        tokenUrl (str): The URL to which the client should be redirected to obtain a token.
        scheme_name (Optional[str], optional): The name of the OAuth2 scheme. Defaults to None.
        scopes (Optional[Dict[str, str]], optional): A dictionary of scopes and their descriptions. Defaults to {}.
        auto_error (bool, optional): Whether to automatically raise an HTTP 401 Unauthorized error
        if the token is not found or is invalid. Defaults to True.

    Attributes:
        flows (OAuthFlowsModel): The OAuth2 flows model, containing the token URL and scopes.

    Methods:
        __call__(self, request: Request) -> Optional[str]:
            Parses the token from the `access_token` cookie in the request and returns it if valid.
            If the token is not found or is invalid, and `auto_error` is True, raises an
            HTTP 401 Unauthorized error. If `auto_error` is False, returns None.
    """

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        """
        Initializes the `OAuth2PasswordBearerWithCookie` class with the provided parameters.

        Parameters:
            tokenUrl (str): The URL to which the client should be redirected to obtain a token.
            scheme_name (Optional[str], optional): The name of the OAuth2 scheme. Defaults to None.
            scopes (Optional[Dict[str, str]], optional): A dictionary of scopes and their descriptions. Defaults to {}.
            auto_error (bool, optional): Whether to automatically raise an HTTP 401 Unauthorized error
            if the token is not found or is invalid. Defaults to True.

        Attributes:
            flows (OAuthFlowsModel): The OAuth2 flows model, containing the token URL and scopes.
        """
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        """
        Parses the token from the `access_token` cookie in the request and returns it if valid.
        If the token is not found or is invalid, and `auto_error` is True, raises an
        HTTP 401 Unauthorized error. If `auto_error` is False, returns None.

        Parameters:
        request (Request): The HTTP request object containing the cookies.

        Returns:
        Optional[str]: The parsed token from the `access_token` cookie, or None if
        the token is not found or is invalid and `auto_error` is False.

        Raises:
        HTTPException: If the token is not found or is invalid and `auto_error` is True.
        """
        authorization = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param
