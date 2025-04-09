import datetime
import json
import logging
import os

from ..utils.authentication import GuardicoreAuth
from ..utils.pagination import PaginatedResponse
from ..utils.sentinel import AzureSentinel
from .models.asset import GuardicoreAsset

SENTINEL_BATCH_SIZE = 1000


async def main(name: str):
    logging.info(f'Starting asset activity that was called by: {name}')
    azure_connection = AzureSentinel(
        workspace_id=os.environ.get('SentinelWorkspaceId', ''),
        workspace_key=os.environ.get('SentinelWorkspaceKey', ''),
        log_analytics_url=os.getenv('logAnalyticsUri', '')
    )
    entities_found = 0
    url = os.environ.get('GuardicoreUrl', '')
    authentication_object = GuardicoreAuth(
        url=url,
        user=os.environ.get('GuardicoreUser', ''),
        password=os.environ.get('GuardicorePassword', '')
    )
    items_batch = []
    async for item in PaginatedResponse(
        endpoint=f'{url}/api/v3.0/assets',
        request_type='GET',
        params={
            'status': 'on'
        },
        authentication=authentication_object).items():
        entities_found += 1
        try:
            items_batch.append(GuardicoreAsset(**item).model_dump())
            if len(items_batch) >= SENTINEL_BATCH_SIZE:
                logging.info(f"Posting {len(items_batch)} assets to Sentinel")
                await azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreAssets')
                logging.info(f"Posted {len(items_batch)} assets to Sentinel")
                items_batch.clear()
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {item}")

    if len(items_batch) > 0:
        try:
            logging.info(f"Posting {len(items_batch)} assets to Sentinel")
            await azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreAssets')
            logging.info(f"Posted {len(items_batch)} assets to Sentinel")
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {items_batch}")
    logging.info(f"Processed {entities_found} connections")
