import datetime
import json
import logging
import os
from threading import Lock

import azure.durable_functions as df
from GuardicoreData.utils.authentication import GuardicoreAuth
from GuardicoreData.utils.pagination import PaginatedResponse
from GuardicoreData.utils.sentinel import AzureSentinel
from GuardicoreData.models.incident import GuardicoreIncident

SENTINEL_BATCH_SIZE = 1000


def incident_fetching(azure_connection: AzureSentinel, context: df.DurableOrchestrationContext, context_lock: Lock):
    logging.info('Starting incident import')
    url = os.environ.get('GuardicoreUrl', '')
    authentication_object = GuardicoreAuth(
        url=url,
        user=os.environ.get('GuardicoreUser', ''),
        password=os.environ.get('GuardicorePassword', '')
    )
    items_batch = []
    datetime_entity_id = df.EntityId("GuardicoreTimestampEntity", "last_incident_time")
    with context_lock:
        connections_last_time = yield context.call_entity(datetime_entity_id, "get",
                                                          {"type": "last_incident_time"})
    if connections_last_time == 0:
        connections_last_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=5)
        connections_last_time = connections_last_time.timestamp() * 1000

    for item in PaginatedResponse(
            endpoint=f'{url}/api/v3.0/incidents',
            request_type='GET',
            params={
                'from_time': connections_last_time,
                'to_time': datetime.datetime.now(tz=datetime.UTC).timestamp() * 1000,
            },
            authentication=authentication_object).items():
        try:
            items_batch.append(GuardicoreIncident(**item).model_dump_json())
            if len(items_batch) >= SENTINEL_BATCH_SIZE:
                logging.info(f"Posting {len(items_batch)} items to Sentinel")
                azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreIncidents')
                last_connection_time = datetime.datetime.fromisoformat(item['db_insert_time']).timestamp() * 1000
                with context_lock:
                    yield context.call_entity(datetime_entity_id, "set",
                                              {"type": "last_incident_time", "time": last_connection_time})
                items_batch.clear()
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {item}")

    if len(items_batch) > 0:
        try:
            azure_connection.post_data(body=json.dumps(items_batch), log_type='GuardicoreIncidents')
            last_connection_time = datetime.datetime.fromisoformat(items_batch[-1]['TimeGenerated']).timestamp() * 1000
            with context_lock:
                yield context.call_entity(datetime_entity_id, "set",
                                          {"type": "last_incident_time", "time": last_connection_time})
        except Exception as e:
            logging.info(type(e))
            logging.error(f"Failed to post data to Sentinel: {e}")
            logging.error(f"Failed data: {items_batch}")
