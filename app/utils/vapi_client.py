from vapi import Vapi
from vapi.calls.client import CallsClient
from vapi.core.client_wrapper import SyncClientWrapper
from vapi.core.api_error import ApiError
from json.decoder import JSONDecodeError
import httpx
from app.config.config import settings


class CustomCallsClient(CallsClient):
    def delete(self, id: str, *, request_options=None):
        _response = self._client_wrapper.httpx_client.request(
            f"call/{id}",
            method="DELETE",
            request_options=request_options,
        )
        # Simply check if the status code indicates success
        if 200 <= _response.status_code < 300:
            return {"success": True, "message": f"Call {id} deleted successfully"}
        # If not successful, raise the error as before
        try:
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)


class CustomVapi(Vapi):
    def __init__(self, token: str):
        # Initialize the base client first
        self.token = token
        self.httpx_client = httpx.Client(
            base_url=settings.VAPI_BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        self._client_wrapper = SyncClientWrapper(self.httpx_client)
        # Initialize our custom calls client
        self.calls = CustomCallsClient(client_wrapper=self._client_wrapper)
