import datetime
import logging
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    logging.info('Executing guardicore orchestration')
    datetime_entity_id = df.EntityId("GuardicoreTimestampEntity", "timestamps")
    connections_last_time = yield context.call_entity(datetime_entity_id, "get",
                                                      {"type": "last_connection_time"})
    incident_last_time = yield context.call_entity(datetime_entity_id, "get",
                                                   {"type": "last_incident_time"})
    today = datetime.datetime.now(tz=datetime.UTC)
    if connections_last_time is None or connections_last_time == "":
        connections_last_time = datetime.datetime.now(tz=datetime.UTC).date()
        context.call_activity("GuardicoreConnectionActivity", "Orchestrator")
    else:
        connections_last_time_date = datetime.datetime.fromisoformat(connections_last_time)
        if connections_last_time_date < today - datetime.timedelta(days=1) and today.hour > 2:
            connections_last_time = datetime.datetime.now(tz=datetime.UTC).date()
            context.call_activity("GuardicoreConnectionActivity", "Orchestrator")

        incident_last_time = datetime.datetime.now(tz=datetime.UTC).date()
        context.call_activity("GuardicoreIncidentActivity", incident_last_time)
    tasks = [
        context.call_activity("GuardicoreConnectionActivity", connections_last_time),
        context.call_activity("GuardicoreIncidentActivity", incident_last_time),
        context.call_activity("GuardicoreAssetActivity", "Orchestrator"),
        context.call_activity("GuardicorePolicyEntity", "Orchestrator"),
        context.call_activity("GuardicoreAgentActivity", "Orchestrator"),
        context.call_activity("GuardicoreLabelActivity", "Orchestrator"),
    ]
    result_data = yield context.task_all(tasks)
    connections_last_time_updated = result_data[0]
    incident_last_time_updated = result_data[1]
    yield context.call_entity(datetime_entity_id, "set",
                              {"type": "last_connection_time",
                               "time": connections_last_time_updated})

    yield context.call_entity(datetime_entity_id, "set",
                              {"type": "last_incident_time",
                               "time": incident_last_time_updated})


main = df.Orchestrator.create(orchestrator_function)
