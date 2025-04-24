import datetime
import os
import croniter
from ..utils.import_logic import run_import_loop
from .models.connection import GuardicoreConnection
import datetime
from datetime import datetime

async def main(name: str):
    connections_last_time = int(name)
    if connections_last_time == 0:
        scheduled_run = os.environ.get("Schedule", "0 */10 * * * *")
        connections_last_time = croniter.croniter(scheduled_run, datetime.now(tz=datetime.UTC)).get_prev(datetime)
        connections_last_time = connections_last_time.timestamp() * 1000

    last_connection_time = int(connections_last_time)

    return await run_import_loop(
        destination_table='GuardicoreConnections',
        api_endpoint='api/v3.0/connections',
        method='GET',
        params={
            'from_time': last_connection_time,
            'to_time': int(datetime.now(tz=datetime.UTC).timestamp()) * 1000,
            'sort': 'slot_start_time'
        },
        model_class=GuardicoreConnection,
        add_sampling_timestamp=False,
        field_name_for_last_timestamp='slot_start_time'
    )
