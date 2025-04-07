import re
import base64
import hmac
import hashlib
import logging
from threading import Lock

import requests
from datetime import datetime


class AzureSentinel:
    def __init__(self, workspace_id: str, workspace_key: str, log_analytics_url=''):
        self._workspace_id = workspace_id
        self._lock = Lock()
        self._workspace_key = workspace_key
        if log_analytics_url in (None, '') or str(log_analytics_url).isspace():
            log_analytics_url = 'https://' + self._workspace_id + '.ods.opinsights.azure.com'

        pattern = r"https:\/\/([\w\-]+)\.ods\.opinsights\.azure.([a-zA-Z\.]+)$"
        if not re.match(pattern, str(log_analytics_url)):
            raise Exception("Invalid Log Analytics Uri.")
        self._log_analytics_url = log_analytics_url

    def build_signature(self, date, content_length, method, content_type, resource):
        x_headers = 'x-ms-date:' + date
        string_to_hash = method + "\n" + \
                         str(content_length) + "\n" + content_type + \
                         "\n" + x_headers + "\n" + resource
        bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
        decoded_key = base64.b64decode(self._workspace_key)
        encoded_hash = base64.b64encode(hmac.new(
            decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
        authorization = "SharedKey {}:{}".format(
            self._workspace_id, encoded_hash)
        return authorization

    def post_data(self, body: str, log_type: str):
        logging.info('constructing post to send to Azure Sentinel.')
        method = 'POST'
        content_type = 'application/json'
        resource = '/api/logs'
        with self._lock:
            rfc1123date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            content_length = len(body)
            signature = self.build_signature(
                rfc1123date, content_length, method, content_type, resource)
            uri = self._log_analytics_url + resource + '?api-version=2016-04-01'
            headers = {
                'content-type': content_type,
                'Authorization': signature,
                'Log-Type': log_type,
                'x-ms-date': rfc1123date
            }
            logging.info('Sending post to Azure Sentinel.')
            response = requests.post(uri, data=body, headers=headers)
            logging.info(response.status_code)
            if 200 <= response.status_code <= 299:
                logging.info(f"{response.content} XDD")
                return response.status_code
            else:
                logging.warning("Events are not processed into Azure. Response code: {}".format(
                    response.status_code))
                raise Exception(
                    f'Sending to Azure Sentinel failed with status code {response.status_code}')
