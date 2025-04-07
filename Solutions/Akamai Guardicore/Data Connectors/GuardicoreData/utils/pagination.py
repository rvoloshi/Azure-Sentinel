import logging
from collections.abc import Callable
from http import HTTPStatus

import requests
from typing import Iterable, Final

from utils.authentication import GuardicoreAuth


class PaginatedResponse:
    ENTITIES_PER_PAGE: Final[int] = 1000
    METHOD_TYPE_TO_FUNCTION: Final[dict[str, Callable]] = {
        'GET': requests.get,
        'POST': requests.post,
        'PUT': requests.put,
    }

    def __init__(self, endpoint: str, request_type: str, authentication: GuardicoreAuth,
                 headers: dict = None, body: dict = None, params: dict = None):
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        self._endpoint = endpoint
        self._authentication = authentication
        self._request_type = request_type
        self._params = params
        self._headers = headers
        self._body = body

    def items(self) -> Iterable[dict]:
        entities_found = 0
        if self._request_type not in PaginatedResponse.METHOD_TYPE_TO_FUNCTION:
            raise ValueError(f"Unsupported request type: {self._request_type}")

        while True:
            self._headers.update(self._authentication.get_authorization_headers())
            self._params.update({"offset": entities_found,
                                 "limit": PaginatedResponse.ENTITIES_PER_PAGE})

            response = PaginatedResponse.METHOD_TYPE_TO_FUNCTION[self._request_type](self._endpoint,
                                                                                     params=self._params,
                                                                                     headers=self._headers,
                                                                                     json=self._body)
            if response.status_code == HTTPStatus.OK.value:
                resp = response.json()
                if 'objects' not in resp:
                    raise ValueError(f"Invalid response format: {resp}")
                for item in resp['objects']:
                    yield item
                entities_found += len(resp['objects'])
                if len(resp['objects']) != PaginatedResponse.ENTITIES_PER_PAGE:
                    logging.info(f"End of pagination reached for {self._endpoint}")
                    break
            elif response.status_code == HTTPStatus.NO_CONTENT.value:
                logging.info(f"No content found in the response for {self._endpoint}")
                break
            else:
                logging.error(f"Failed to fetch data from {self._endpoint}. Status code: {response.status_code}")
                logging.error(f"Response: {response.text}")
                break
