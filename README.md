# kedro-spaceflights-dagster

![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)
[![Code style: ruff-format](https://img.shields.io/badge/code%20style-ruff_format-6340ac.svg)](https://github.com/astral-sh/ruff)

This repository aims at exploring how [Dagster](https://dagster.io/) can be used to orchestrate [Kedro](https://kedro.org/) pipelines. It is based on the [Kedro Spaceflights tutorial](https://kedro.readthedocs.io/en/stable/04_user_guide/01_kedro_project_setup/spaceflights_tutorial.html) and on @astrojuanlu's [copier-kedro](https://github.com/astrojuanlu/copier-kedro) template.

## Starting the Dagster UI
To start the Dagster UI web server:

```bash
dagster dev
```

Open http://localhost:3000 with your browser to see the project.

The assets are automatically loaded into the Dagster code location as you define them.

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