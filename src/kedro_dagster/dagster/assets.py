"""Define Dagster assets from Kedro nodes."""

from collections.abc import Callable
from pathlib import Path

from dagster import (
    AssetIn,
    AssetOut,
    AssetSpec,
    Config,
    get_dagster_logger,
    multi_asset,
)
from kedro.framework.hooks.manager import _create_hook_manager
from kedro.framework.project import pipelines
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataset
from kedro.pipeline.node import Node
from kedro.runner import run_node
from pydantic import create_model


def kedro_init(
    pipeline_name: str,
    project_path: Path,
    env: str,
):
    """Initialize a Kedro session and returns the DataCatalog and KedroSession.

    Args:
        pipeline_name (str): The name of the pipeline to initialize.
        project_path (Path): The path to the Kedro project.
        env (str): Kedro environment to load the catalog and the parameters from.

    Returns: A tuple containing the DataCatalog and KedroSession objects.
    """
    # bootstrap project within task / flow scope
    logger = get_dagster_logger()

    logger.info("Bootstrapping project")
    bootstrap_project(project_path)

    session = KedroSession.create(
        project_path=project_path,
        env=env,
    )

    # Note that for logging inside a Prefect task logger is used.
    logger.info("Session created with ID %s", session.session_id)
    pipeline = pipelines.get(pipeline_name)

    logger.info("Loading context...")
    context = session.load_context()
    catalog = context.catalog

    logger.info("Registering datasets...")
    memory_asset_names = pipeline.datasets() - set(catalog.list())
    for asset_name in memory_asset_names:
        catalog.add(asset_name, MemoryDataset())

    return catalog, session.session_id, memory_asset_names


def define_node_multi_asset(
    node: Node,
    pipeline_name: str,
    catalog: DataCatalog,
    session_id: str,
    memory_asset_names: list,
) -> Callable:
    """Wrap a kedro Node inside a Dagster multi asset.

    Args:
        node: Kedro node for which a Prefect task is being created.
        pipeline_name: Name of the pipeline that the node belongs to.
        catalog: DataCatalog object that contains the datasets used by the node.
        session_id: ID of the Kedro session that the node will be executed in.
        memory_asset_names: List of dataset names that are defined in the `catalog`
        as `MemoryDataset`s.

    Returns: Dagster multi assset function that wraps the Kedro node.
    """
    output_asset_names = node.outputs
    input_asset_names = [
        input_name for input_name in node.inputs if not input_name.startswith("params:")
    ]
    input_memory_asset_names = [
        asset_name
        for asset_name in memory_asset_names
        if asset_name in input_asset_names
    ]
    dep_asset_names = [
        asset_name
        for asset_name in input_asset_names
        if asset_name not in input_memory_asset_names
    ]
    param_names = [
        input_name for input_name in node.inputs if input_name.startswith("params:")
    ]

    # TODO: Improve so that params render properly
    params = {param_name: catalog.load(param_name) for param_name in param_names}
    NodeParameters = create_model(
        "MemoryDatasetConfig",
        **{param_name: (type(param), param) for param_name, param in params.items()},
    )

    class NodeParametersConfig(NodeParameters, Config, extra="allow", frozen=False):
        pass

    outs = {asset_name: AssetOut() for asset_name in output_asset_names}
    if not len(node.outputs):
        outs = {node.name: AssetOut()}

    # Define a multi_asset for nodes with multiple outputs
    @multi_asset(
        name=node.name,
        group_name=pipeline_name,
        ins={asset_name: AssetIn() for asset_name in input_memory_asset_names},
        outs=outs,
        deps=dep_asset_names,
        op_tags=node.tags,
    )
    def dagster_asset(config: NodeParametersConfig, **kwargs):  # TODO: Use context?
        for asset_name in input_memory_asset_names:
            catalog.save(asset_name, kwargs[asset_name])

        # Logic to execute the Kedro node
        run_node(
            node,
            catalog,
            _create_hook_manager(),
            session_id,
        )

        output_assets = [catalog.load(asset_name) for asset_name in output_asset_names]
        return tuple(output_assets)

    return dagster_asset


def get_node_pipeline_name(pipelines, node):
    """Return the name of the pipeline that a node belongs to.

    Args:
        pipelines: Dictionary of Kedro pipelines.
        node: Kedro node for which the pipeline name is being retrieved.

    Returns: Name of the pipeline that the node belongs to.
    """
    for pipeline_name, pipeline in pipelines.items():
        for pipeline_node in pipeline.nodes:
            if node.name == pipeline_node.name:
                return pipeline_name


def load_kedro_assets_from_pipeline(env: str | None = None):
    """Load Kedro assets from a pipeline into Dagster.

    Args
        env: Kedro environment to load the catalog and parameters from.

    Returns: List of Dagster assets.
    """
    logger = get_dagster_logger()
    pipeline_name = "__default__"
    project_path = Path.cwd()

    metadata = bootstrap_project(project_path)
    logger.info("Project name: %s", metadata.project_name)

    logger.info("Initializing Kedro...")
    catalog, session_id, memory_asset_names = kedro_init(
        pipeline_name=pipeline_name, project_path=project_path, env=env
    )
    pipeline = pipelines.pop(pipeline_name)

    logger.info("Building asset list...")
    assets = []
    for external_asset in pipeline.inputs():
        if external_asset.startswith("params:"):
            continue
        asset = AssetSpec(external_asset, group_name="external")
        assets.append(asset)

    for node in pipeline.nodes:
        node_pipeline_name = get_node_pipeline_name(pipelines, node)

        asset = define_node_multi_asset(
            node,
            node_pipeline_name,
            catalog,
            session_id,
            memory_asset_names,
        )
        assets.append(asset)

    return assets
