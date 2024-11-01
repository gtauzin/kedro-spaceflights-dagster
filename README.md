# kedro-dagster

![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)
[![Code style: ruff-format](https://img.shields.io/badge/code%20style-ruff_format-6340ac.svg)](https://github.com/astral-sh/ruff)

(Add a longer description here.)

## How to create your first Kedro pipeline

To list the available Kedro pipelines:

```
uv run kedro registry list
```

And to create a new one:

```
uv run kedro pipeline create data_processing
```

See the [documentation on modular pipelines](https://docs.kedro.org/en/stable/nodes_and_pipelines/modular_pipelines.html)
for more information.

## How to run your Kedro pipeline

You can run your Kedro project with:

```
uv run kedro run
```

## How to test your Kedro project

Have a look at the file `tests/test_run.py` for instructions on how to write your tests. You can run your tests as follows:

```
uv run pytest
```

## Project dependencies

To see and update the dependency requirements for your project, use `uv`.

# kedro_dagster

This is a [Dagster](https://dagster.io/) project scaffolded with [`dagster project scaffold`](https://docs.dagster.io/getting-started/create-new-project).

## Getting started

First, install your Dagster code location as a Python package. By using the --editable flag, pip will install your Python package in ["editable mode"](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs) so that as you develop, local code changes will automatically apply.

```bash
pip install -e ".[dev]"
```

Then, start the Dagster UI web server:

```bash
dagster dev
```

Open http://localhost:3000 with your browser to see the project.

You can start writing assets in `kedro_dagster/assets.py`. The assets are automatically loaded into the Dagster code location as you define them.

## Development

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### Unit testing

Tests are in the `kedro_dagster_tests` directory and you can run tests using `pytest`:

```bash
pytest kedro_dagster_tests
```

### Schedules and sensors

If you want to enable Dagster [Schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules) or [Sensors](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors) for your jobs, the [Dagster Daemon](https://docs.dagster.io/deployment/dagster-daemon) process must be running. This is done automatically when you run `dagster dev`.

Once your Dagster Daemon is running, you can start turning on schedules and sensors for your jobs.

## Deploy on Dagster Cloud

The easiest way to deploy your Dagster project is to use Dagster Cloud.

Check out the [Dagster Cloud Documentation](https://docs.dagster.cloud) to learn more.
