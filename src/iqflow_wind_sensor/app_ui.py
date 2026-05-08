from pathlib import Path

from pydoover import ui

from .app_tags import IQFlowWindSensorTags


# Beaufort-inspired bands, sized for km/h (the default wind_units config).
# If the device is reconfigured to mps/knots the boundaries won't line up.
_WIND_SPEED_RANGES = [
    ui.Range("Calm", 0, 20, ui.Colour.green),
    ui.Range("Moderate", 20, 40, ui.Colour.blue),
    ui.Range("Strong", 40, 62, ui.Colour.yellow),
    ui.Range("Gale+", 62, 150, ui.Colour.red),
]

_WIND_GUST_RANGES = [
    ui.Range("Calm", 0, 25, ui.Colour.green),
    ui.Range("Moderate", 25, 50, ui.Colour.blue),
    ui.Range("Strong", 50, 75, ui.Colour.yellow),
    ui.Range("Gale+", 75, 180, ui.Colour.red),
]


class IQFlowWindSensorUI(ui.UI):
    history = ui.Multiplot(
        "Wind History",
        name="windHistory",
        series=[
            ui.Series(
                "Wind Speed",
                value=IQFlowWindSensorTags.wind_speed,
                name="windSpeed",
                data_type="number",
                colour=ui.Colour.blue,
                active=True,
            ),
            ui.Series(
                "Wind Gust",
                value=IQFlowWindSensorTags.wind_gust,
                name="windGust",
                data_type="number",
                colour=ui.Colour.tomato,
                active=True,
            ),
            ui.Series(
                "Wind Direction (°)",
                value=IQFlowWindSensorTags.wind_direction_degrees,
                name="windDirection",
                data_type="number",
                colour=ui.Colour.purple,
                shared_axis=False,
                active=False,
            ),
        ],
    )

    wind_speed = ui.NumericVariable(
        "Wind Speed",
        value=IQFlowWindSensorTags.wind_speed,
        precision=1,
        ranges=_WIND_SPEED_RANGES,
    )
    wind_gust = ui.NumericVariable(
        "Wind Gust",
        value=IQFlowWindSensorTags.wind_gust,
        precision=1,
        ranges=_WIND_GUST_RANGES,
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
