import datetime
import json
import logging
import os

from GuardicoreDataImporter.utils.authentication import GuardicoreAuth
from GuardicoreDataImporter.utils.pagination import PaginatedResponse
from GuardicoreDataImporter.utils.sentinel import AzureSentinel
from GuardicoreDataImporter.models.incident import GuardicoreIncident

SENTINEL_BATCH_SIZE = 1000


async def incident_fetching(azure_connection: AzureSentinel, connections_last_time: int = 0):
    logging.info('Starting incident import')
    url = os.environ.get('GuardicoreUrl', '')
    authentication_object = GuardicoreAuth(
        url=url,
        user=os.environ.get('GuardicoreUser', ''),
        password=os.environ.get('GuardicorePassword', '')
    )
    items_batch = []
    entities_processed = 0
    if connections_last_time == 0:
        connections_last_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=5)
        connections_last_time = connections_last_time.timestamp() * 1000

    last_connection_time = int(connections_last_time)
    logging.info(
        f"from_time: {last_connection_time}, to_time: {int(datetime.datetime.now(tz=datetime.UTC).timestamp()) * 1000}")
    async for item in PaginatedResponse(
            endpoint=f'{url}/api/v3.0/incidents',
            request_type='GET',
            params={
                'from_time': last_connection_time,
                'to_time': int(datetime.datetime.now(tz=datetime.UTC).timestamp()) * 1000,
            },
            authentication=authentication_object).items():
        entities_processed += 1
        try:
            items_batch.append(GuardicoreIncident(**item).model_dump_json())
            if len(items_batch) >= SENTINEL_BATCH_SIZE:
                logging.info(f"Posting {len(items_batch)} incidents to Sentinel")
                await azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreIncidents')
                logging.info(f"Posted {len(items_batch)} incidents to Sentinel")
                items_batch.clear()
            event_time = int(item['start_time'])
            if event_time > last_connection_time:
                last_connection_time = event_time
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {item}")

    if len(items_batch) > 0:
        try:
            logging.info(f"Posting {len(items_batch)} incidents to Sentinel")
            await azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreIncidents')
            logging.info(f"Posted {len(items_batch)} incidents to Sentinel")
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {items_batch}")
    logging.info(f"Processed {entities_processed} incidents")
    return last_connection_time
