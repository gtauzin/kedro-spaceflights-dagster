# kedro-spaceflights-dagster

![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)
[![Code style: ruff-format](https://img.shields.io/badge/code%20style-ruff_format-6340ac.svg)](https://github.com/astral-sh/ruff)

This repository aims at exploring how [Dagster](https://dagster.io/) can be used to orchestrate [Kedro](https://kedro.org/) pipelines. It is based on the [Kedro Spaceflights tutorial](https://kedro.readthedocs.io/en/stable/04_user_guide/01_kedro_project_setup/spaceflights_tutorial.html) and on @astrojuanlu's [copier-kedro](https://github.com/astrojuanlu/copier-kedro) template.

## Starting the Dagster UI
To start the Dagster UI web server:

```bash
uv run dagster dev
```

Open http://localhost:3000 with your browser to see the project.

The assets are automatically loaded into the Dagster code location as you define them.