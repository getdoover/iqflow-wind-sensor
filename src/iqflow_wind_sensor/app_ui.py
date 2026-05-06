from pathlib import Path

from pydoover import ui

from .app_tags import IQFlowWindSensorTags


class IQFlowWindSensorUI(ui.UI):
    wind_speed = ui.NumericVariable(
        "Wind Speed",
        value=IQFlowWindSensorTags.wind_speed,
        precision=1,
    )
    wind_gust = ui.NumericVariable(
        "Wind Gust",
        value=IQFlowWindSensorTags.wind_gust,
        precision=1,
    )
    wind_direction_degrees = ui.NumericVariable(
        "Wind Direction (°)",
        value=IQFlowWindSensorTags.wind_direction_degrees,
        precision=0,
    )
    wind_direction_compass = ui.TextVariable(
        "Wind Direction",
        value=IQFlowWindSensorTags.wind_direction_compass,
    )
    comms_ok = ui.BooleanVariable(
        "Sensor Communicating",
        value=IQFlowWindSensorTags.comms_ok,
    )


def export():
    IQFlowWindSensorUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "iqflow_wind_sensor",
    )
