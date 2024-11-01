from collections.abc import Callable
from pathlib import Path

from dagster import (
    AssetIn,
    AssetOut,
    Config,
    Definitions,
    In,
    get_dagster_logger,
    job,
    multi_asset,
    op,
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
    """
    Initializes a Kedro session and returns the DataCatalog and KedroSession.


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


def define_node_asset(
    node: Node,
    pipeline_name: str,
    catalog: DataCatalog,
    session_id: str,
    memory_asset_names: list,
) -> Callable:
    """
    Function that wraps a Node inside a task for future execution

    Args:
        node: Kedro node for which a Prefect task is being created.
        execution_config: The configurations required for the node to execute
        that includes catalogs and session id

    Returns: Prefect task for the passed node.

    """
    logger = get_dagster_logger()

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

    # Define a multi_asset for nodes with multiple outputs
    @multi_asset(
        name=node.name,
        group_name=pipeline_name,
        ins={asset_name: AssetIn() for asset_name in input_memory_asset_names},
        outs={asset_name: AssetOut() for asset_name in output_asset_names},
        deps=dep_asset_names,
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


def define_node_op_job(
    node: Node,
    pipeline_name: str,
    catalog: DataCatalog,
    session_id: str,
    memory_asset_names: list,
    assets: list,
) -> Callable:
    """
    Function that wraps a Node inside a task for future execution

    Args:
        node: Kedro node for which a Prefect task is being created.
        execution_config: The configurations required for the node to execute
        that includes catalogs and session id

    Returns: Prefect task for the passed node.

    """
    logger = get_dagster_logger()

    input_asset_names = [
        input_name for input_name in node.inputs if not input_name.startswith("params:")
    ]
    input_memory_asset_names = [
        asset_name
        for asset_name in memory_asset_names
        if asset_name in input_asset_names
    ]
    input_asset_specs = {
        key.path[0]: asset.get_asset_spec(key) for asset in assets for key in asset.keys
    }
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

    # Define a multi_asset for nodes with multiple outputs
    @op(
        name=node.name + "_op",
        ins={asset_name: In() for asset_name in input_asset_names},
    )
    def dagster_op(
        config: NodeParametersConfig, **kwargs
    ) -> None:  # TODO: Use context?
        for asset_name in input_memory_asset_names:
            catalog.save(asset_name, kwargs[asset_name])

        # Logic to execute the Kedro node
        run_node(
            node,
            catalog,
            _create_hook_manager(),
            session_id,
        )

    @job(
        name=node.name,
        # group_name=pipeline_name,
    )
    def dagster_op_job():
        asset_specs = {
            asset_name: asset_specs
            for asset_name, asset_specs in input_asset_specs.items()
            if asset_name in input_asset_names
        }
        # asset.get_asset_spec(key=asset_name)
        # get_asset_spec(key="X_test"))
        # for asset in assets# if asset_name in asset.keys

        #     for asset_name in input_asset_names
        # }
        dagster_op(**asset_specs)

    return dagster_op_job


def get_node_pipeline_name(pipelines, node):
    for pipeline_name, pipeline in pipelines.items():
        for pipeline_node in pipeline.nodes:
            if node.name == pipeline_node.name:
                return pipeline_name


def load_kedro_assets_from_pipeline(
    pipeline_name: str = "__default__", env: str | None = None
):
    logger = get_dagster_logger()
    project_path = Path.cwd()

    metadata = bootstrap_project(project_path)
    logger.info("Project name: %s", metadata.project_name)

    logger.info("Initializing Kedro...")
    catalog, session_id, memory_asset_names = kedro_init(
        pipeline_name=pipeline_name, project_path=project_path, env=env
    )
    pipeline = pipelines.pop(pipeline_name)

    logger.info("Building asset and op job lists...")
    assets, op_jobs = [], []
    for node in pipeline.nodes:
        node_pipeline_name = get_node_pipeline_name(pipelines, node)

        if len(node.outputs):
            asset = define_node_asset(
                node,
                node_pipeline_name,
                catalog,
                session_id,
                memory_asset_names,
            )
            assets.append(asset)

        else:
            op_job = define_node_op_job(
                node,
                node_pipeline_name,
                catalog,
                session_id,
                memory_asset_names,
                assets,
            )
            op_jobs.append(op_job)

    return assets, op_jobs


all_assets, all_op_jobs = load_kedro_assets_from_pipeline()


defs = Definitions(
    assets=all_assets,
    jobs=all_op_jobs,
)
