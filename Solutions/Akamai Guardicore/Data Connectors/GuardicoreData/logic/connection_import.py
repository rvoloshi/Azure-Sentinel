import datetime
import json
import logging
import os

from GuardicoreData.utils.authentication import GuardicoreAuth
from GuardicoreData.utils.pagination import PaginatedResponse
from GuardicoreData.utils.sentinel import AzureSentinel
from GuardicoreData.models.connection import GuardicoreConnection

SENTINEL_BATCH_SIZE = 1000


async def connection_fetching(azure_connection: AzureSentinel, connections_last_time: int = 0):
    logging.info('Starting connection import')
    entities_found = 0
    url = os.environ.get('GuardicoreUrl', '')
    authentication_object = GuardicoreAuth(
        url=url,
        user=os.environ.get('GuardicoreUser', ''),
        password=os.environ.get('GuardicorePassword', '')
    )
    items_batch = []
    if connections_last_time == 0:
        connections_last_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=5)
        connections_last_time = connections_last_time.timestamp() * 1000

    last_connection_time = int(connections_last_time)
    logging.info(
        f"from_time: {connections_last_time}, to_time: {int(datetime.datetime.now(tz=datetime.UTC).timestamp()) * 1000}")
    async for item in PaginatedResponse(
            endpoint=f'{url}/api/v3.0/connections',
            request_type='GET',
            params={
                'from_time': last_connection_time,
                'to_time': int(datetime.datetime.now(tz=datetime.UTC).timestamp()) * 1000,
            },
            authentication=authentication_object).items():
        entities_found += 1
        try:
            items_batch.append(GuardicoreConnection(**item).model_dump_json())
            if len(items_batch) >= SENTINEL_BATCH_SIZE:
                logging.info(f"Posting {len(items_batch)} items to Sentinel")
                await azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreConnections')
                items_batch.clear()
            last_connection_time = int(datetime.datetime.fromisoformat(item['db_insert_time']).timestamp()) * 1000
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {item}")

    if len(items_batch) > 0:
        try:
            await azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreConnections')
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {items_batch}")
    logging.info(f"Processed {entities_found} connections")
    return last_connection_time
