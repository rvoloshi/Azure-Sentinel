import asyncio
import logging
import os

from GuardicoreDataImporter.utils.sentinel import AzureSentinel
from GuardicoreDataImporter.logic.incident_import import incident_fetching
from GuardicoreDataImporter.logic.connection_import import connection_fetching
import azure.durable_functions as df


def main_execution(context: df.DurableOrchestrationContext):
    logging.info('Starting guardicore data import')
    sentinel = AzureSentinel(
        workspace_id=os.environ.get('SentinelWorkspaceId', ''),
        workspace_key=os.environ.get('SentinelWorkspaceKey', ''),
        log_analytics_url=os.getenv('logAnalyticsUri', '')
    )
    datetime_entity_id = df.EntityId("GuardicoreTimestampEntity", "last_connection_time")
    connections_last_time = yield context.call_entity(datetime_entity_id, "get",
                                                      {"type": "last_connection_time"})
    incident_last_time = yield context.call_entity(datetime_entity_id, "get", {
        "type": "last_incident_time"})
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result_data = loop.run_until_complete(asyncio.gather(
        connection_fetching(sentinel, connections_last_time),
        incident_fetching(sentinel, incident_last_time),
        return_exceptions=True
    ))
    connections_last_time_updated = result_data[0]
    incident_last_time_updated = result_data[1]

    try:
        yield context.call_entity(datetime_entity_id, "set",
                                  {"type": "last_connection_time", "time": connections_last_time_updated})
    except Exception as e:
        logging.error(f"Failed to update connection last time: {e}")
    try:
        yield context.call_entity(datetime_entity_id, "set",
                              {"type": "last_incident_time", "time": incident_last_time_updated})
    except Exception as e:
        logging.error(f"Failed to update incident last time: {e}")


main = df.Orchestrator.create(main_execution)
