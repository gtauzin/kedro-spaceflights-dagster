"""Dagster definition."""

from dagster import Definitions

from .assets import load_kedro_assets_from_pipeline

all_assets = load_kedro_assets_from_pipeline()


defs = Definitions(
    assets=all_assets,
)
