from pathlib import Path

from pydoover import ui

from .app_tags import IQFlowWindSensorTags


class IQFlowWindSensorUI(ui.UI):
    wind_speed = ui.NumericVariable(
        "Wind Speed",
        value=IQFlowWindSensorTags.wind_speed,
        name="wind_speed",
        precision=1,
        position=1,
    )
    wind_gust = ui.NumericVariable(
        "Wind Gust",
        value=IQFlowWindSensorTags.wind_gust,
        name="wind_gust",
        precision=1,
        position=2,
    )
    wind_direction_degrees = ui.NumericVariable(
        "Wind Direction (°)",
        value=IQFlowWindSensorTags.wind_direction_degrees,
        name="wind_direction_degrees",
        precision=0,
        position=3,
    )
    wind_direction_compass = ui.TextVariable(
        "Wind Direction",
        value=IQFlowWindSensorTags.wind_direction_compass,
        name="wind_direction_compass",
        position=4,
    )
    comms_ok = ui.BooleanVariable(
        "Sensor Communicating",
        value=IQFlowWindSensorTags.comms_ok,
        name="comms_ok",
        position=5,
    )


def export():
    IQFlowWindSensorUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "iqflow_wind_sensor",
    )


if __name__ == "__main__":
    export()
