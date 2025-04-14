import datetime
import json
import logging
import os

from .models.agent import GuardicoreAgent
from ..utils.authentication import GuardicoreAuth
from ..utils.pagination import PaginatedResponse
from ..utils.sentinel import AzureSentinel

SENTINEL_BATCH_SIZE = 1000


async def main(name: str):
    logging.info(f'Starting agents activity that was called by: {name}')
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
    sampling_timestamp = int(datetime.datetime.now(tz=datetime.UTC).timestamp())
    async for item in PaginatedResponse(
        endpoint=f'{url}/api/v3.0/agents',
        request_type='GET',
        authentication=authentication_object).items():
        entities_found += 1
        try:
            full_data = {**item, 'sampling_timestamp': sampling_timestamp}
            items_batch.append(GuardicoreAgent(**full_data).model_dump())
            if len(items_batch) >= SENTINEL_BATCH_SIZE:
                logging.info(f"Posting {len(items_batch)} agents to Sentinel")
                await azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreAgents')
                logging.info(f"Posted {len(items_batch)} agents to Sentinel")
                items_batch.clear()
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {item}")

    if len(items_batch) > 0:
        try:
            logging.info(f"Posting {len(items_batch)} agents to Sentinel")
            await azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreAgents')
            logging.info(f"Posted {len(items_batch)} agents to Sentinel")
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {items_batch}")
    logging.info(f"Processed {entities_found} agents")
