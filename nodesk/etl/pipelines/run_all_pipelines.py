from .critical_projects import run as run_critical_projects
from .evolution_chart import evolution_chart_pipeline

PIPELINES = [run_critical_projects, evolution_chart_pipeline]


def run_all() -> None:
    for pipeline in PIPELINES:
        result = pipeline()
        print(result)


if __name__ == "__main__":
    run_all()
