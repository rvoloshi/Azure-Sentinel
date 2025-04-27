import asyncio
import datetime
import gzip
import io
import json
import os
import logging

import aiohttp
from pydantic import ValidationError
from typing import AsyncGenerator, Final
from datetime import UTC, datetime, timedelta

from .models.connection import GuardicoreConnection
from ..utils.authentication import GuardicoreAuth
from ..utils.sentinel import AzureSentinel


class ConnectionsTaskError(Exception):
    pass


class ConnectionProvider:
    POLL_INTERVAL_SECONDS: Final[int] = 5

    def __init__(self, centra_url: str, user: str, password: str, index_day: str):
        self._authentication_object = GuardicoreAuth(
            url=centra_url,
            user=user,
            password=password
        )
        self._centra_url = centra_url
        self._index_day = index_day
        logging.info(f"ConnectionProvider initialized for index_day: {self._index_day}")

    async def _create_task(self, session: aiohttp.ClientSession) -> str:
        create_url = f"{self._centra_url}/api/v4.0/daily_connections/task"
        payload = {
            "index_day": self._index_day,
            "filters": {},
            "fields": []
        }
        logging.info(f"Creating daily connections task for day: {self._index_day}")
        async with session.post(create_url,
                                headers=await self._authentication_object.get_authorization_headers(),
                                json=payload) as response:
            if response.status == 200:
                result = await response.json()
                task_id = result.get("task_id")
                if task_id:
                    logging.info(f"Task created successfully with ID: {task_id}")
                    return task_id
                else:
                    logging.error(f"Failed to get task_id from response: {result}")
                    raise ConnectionsTaskError(f"Failed to get task_id from response: {result}")
            else:
                error_text = await response.text()
                logging.error(f"Failed to create daily connections task: {response.status}, {error_text}")
                raise ConnectionsTaskError(f"Failed to create daily connections task: {response.status}, {error_text}")

    async def _poll_task_status(self, session: aiohttp.ClientSession, task_id: str) -> int:
        status_url = f"{self._centra_url}/api/v4.0/daily_connections/task/{task_id}"
        status = "NOT DONE"
        connection_count = 0
        logging.info(f"Polling status for task ID: {task_id}")
        while status != "DONE":
            await asyncio.sleep(ConnectionProvider.POLL_INTERVAL_SECONDS)
            try:
                async with session.get(status_url,
                                       headers=await self._authentication_object.get_authorization_headers()) as response:
                    if response.status == 200:
                        result = await response.json()
                        status = result.get("status", "NOT DONE")
                        connection_count = result.get("connections_count", 0)
                        logging.debug(f"Task {task_id} status: {status}, Count: {connection_count}")
                        if status == "FAILED":
                            logging.error(f"Task {task_id} failed. Result: {result}")
                            raise ConnectionsTaskError(f"Task {task_id} failed.")
                        else:
                            logging.info(
                                f"Task {task_id} is still in progress. Status: {status}, Count: {connection_count}")
                    else:
                        error_text = await response.text()
                        logging.warning(
                            f"Failed to get task status for {task_id}: {response.status}, {error_text}. Retrying...")
                        status = "NOT DONE"
            except aiohttp.ClientError as e:
                logging.warning(f"Network error polling task {task_id}: {e}. Retrying...")
                status = "NOT DONE"
            except json.JSONDecodeError as e:
                logging.warning(f"Error decoding status response for task {task_id}: {e}. Retrying...")
                status = "NOT DONE"

        logging.info(f"Task {task_id} is DONE. Expected connections: {connection_count}")
        return connection_count

    async def _download_and_process_data(self, session: aiohttp.ClientSession, task_id: str, connection_count: int) -> \
            AsyncGenerator[GuardicoreConnection, None]:
        download_url = f"{self._centra_url}/api/v4.0/daily_connections/task/{task_id}/download"
        logging.info(f"Downloading data for task ID: {task_id}")
        async with session.get(download_url,
                               headers=await self._authentication_object.get_authorization_headers()) as response:
            if response.status == 200:
                logging.info(f"Successfully started download stream for task {task_id}.")
                buffer = io.BytesIO()
                bytes_read = 0
                async for chunk in response.content.iter_any():
                    buffer.write(chunk)
                    bytes_read += len(chunk)
                    logging.debug(f"Downloaded {bytes_read} bytes for task {task_id}")

                buffer.seek(0)
                processed_lines = 0
                try:
                    with gzip.GzipFile(fileobj=buffer, mode='rb') as gzipped_file:
                        for line_bytes in gzipped_file:
                            try:
                                line_str = line_bytes.decode('utf-8')
                                connection_data = json.loads(line_str)
                                processed_lines += 1
                                try:
                                    yield GuardicoreConnection(**connection_data)
                                except ValidationError as e:
                                    logging.error(f"Failed to validate connection: {e}. Data: {connection_data}")

                                if connection_count > 0 and processed_lines % 1000 == 0:
                                    percentage = (processed_lines / connection_count) * 100
                                    logging.info(
                                        f"Processing task {task_id}... {percentage:.2f}% complete ({processed_lines}/{connection_count})")

                            except json.JSONDecodeError:
                                logging.warning(
                                    f"Skipping invalid JSON line in task {task_id}: {line_bytes[:200]}...")
                                continue
                            except UnicodeDecodeError:
                                logging.warning(
                                    f"Skipping line with decoding error in task {task_id}: {line_bytes[:200]}...")
                                continue
                except gzip.BadGzipFile:
                    logging.error(f"Downloaded file for task {task_id} is not a valid Gzip file or is corrupted.")
                    raise ConnectionsTaskError(f"Invalid Gzip file for task {task_id}")
                except EOFError:
                    logging.error(
                        f"Unexpected end of file while decompressing Gzip for task {task_id}. File might be truncated.")
                    raise ConnectionsTaskError(f"Truncated Gzip file for task {task_id}")

                logging.info(f"Finished processing {processed_lines} lines for task {task_id}.")
            else:
                error_text = await response.text()
                logging.error(f"Failed to download data for task {task_id}: {response.status}, {error_text}")
                raise ConnectionsTaskError(f"Failed to download data: {response.status}, {error_text}")

    async def get_connections(self) -> AsyncGenerator[GuardicoreConnection, None]:
        async with aiohttp.ClientSession() as session:
            task_id = None
            try:
                task_id = await self._create_task(session)
                connection_count = await self._poll_task_status(session, task_id)
                if connection_count > 0:
                    async for connection in self._download_and_process_data(session, task_id, connection_count):
                        yield connection
                else:
                    logging.info(
                        f"Task {task_id} reported 0 connections for day {self._index_day}. No data to process.")

            except ConnectionsTaskError as e:
                logging.error(f"Connection retrieval failed: {e}")
                raise
            except aiohttp.ClientError as e:
                logging.error(f"HTTP Client error during connection retrieval: {e}")
                raise ConnectionsTaskError(f"HTTP Client error: {e}") from e
            except Exception as e:
                logging.exception(f"An unexpected error occurred in get_connections: {e}")
                raise ConnectionsTaskError(f"Unexpected error: {e}") from e


SENTINEL_MAX_CONNECTIONS_PER_REQUEST: Final[int] = 10000


async def main(name: str):
    sentinel = AzureSentinel(
        workspace_id=os.environ.get('SentinelWorkspaceId', ''),
        workspace_key=os.environ.get('SentinelWorkspaceKey', ''),
        log_analytics_url=os.getenv('logAnalyticsUri', '')
    )
    start_time = datetime.now(UTC)
    index_day = datetime.now(UTC).date() - timedelta(days=1)
    index_day_str = index_day.strftime('%Y_%m_%d')
    logging.info(f"Fetching connections for the entire day: {index_day_str}")

    connection_provider = ConnectionProvider(
        centra_url=os.environ.get('GuardicoreUrl', ''),
        user=os.environ.get('GuardicoreUser', ''),
        password=os.environ.get('GuardicorePassword', ''),
        index_day=index_day_str
    )

    guardicore_connections_batch = []
    total_connections_processed = 0
    try:
        async for conn in connection_provider.get_connections():
            guardicore_connections_batch.append(conn.model_dump())
            total_connections_processed += 1

            if len(guardicore_connections_batch) >= SENTINEL_MAX_CONNECTIONS_PER_REQUEST:
                try:
                    await sentinel.post_data(body=json.dumps(guardicore_connections_batch),
                                             log_type='GuardicoreConnection')
                    logging.info(f"Posted {len(guardicore_connections_batch)} connections to Sentinel")
                except Exception as e:
                    logging.error(
                        f"Failed to post batch of {len(guardicore_connections_batch)} connections to Sentinel: {e}")
                guardicore_connections_batch.clear()

        if guardicore_connections_batch:
            try:
                await sentinel.post_data(body=json.dumps(guardicore_connections_batch),
                                         log_type='GuardicoreConnection')
                logging.info(f"Posted final batch of {len(guardicore_connections_batch)} connections to Sentinel")
            except Exception as e:
                logging.error(
                    f"Failed to post final batch of {len(guardicore_connections_batch)} connections to Sentinel: {e}")
            guardicore_connections_batch.clear()
        logging.info(f"Successfully processed {total_connections_processed} connections for {index_day_str}.")
    except ConnectionsTaskError as e:
        logging.error(f"Failed to retrieve connections: {e}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred during main execution for {index_day_str}")
    return start_time.isoformat()

