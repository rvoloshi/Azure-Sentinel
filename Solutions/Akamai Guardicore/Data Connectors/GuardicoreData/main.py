import logging
import os
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock

from GuardicoreData.utils.sentinel import AzureSentinel
from logic.incident_import import incident_fetching
from logic.connection_import import connection_fetching
import azure.durable_functions as df


def main_execution(context: df.DurableOrchestrationContext):
    logging.info('Starting guardicore data import')
    futures = []
    sentinel = AzureSentinel(
        workspace_id=os.environ.get('SentinelWorkspaceId', ''),
        workspace_key=os.environ.get('SentinelWorkspaceKey', ''),
        log_analytics_url=os.getenv('logAnalyticsUri', '')
    )
    context_lock = Lock()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures.append(executor.submit(connection_fetching, sentinel, context, context_lock))
        futures.append(executor.submit(incident_fetching, sentinel, context, context_lock))
    for future in futures:
        try:
            future.result()
        except Exception as e:
            logging.error(f"An error occurred: {e}")
    yield

main = df.Orchestrator.create(main_execution)
