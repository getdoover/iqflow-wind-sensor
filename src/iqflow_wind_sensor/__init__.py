from pydoover.docker import run_app

from .application import IQFlowWindSensorApplication


def main():
    """Run the IQFlow wind sensor application."""
    run_app(IQFlowWindSensorApplication())
