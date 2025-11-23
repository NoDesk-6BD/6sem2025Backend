from .critical_projects import run as run_critical_projects
from .evolution_chart import evolution_chart_pipeline
from .expired_tickets import run as run_expired_tickets
from .expired_tickets_list import run as run_expired_tickets_list
from .companies import run as run_companies

PIPELINES = [
    run_critical_projects,
    evolution_chart_pipeline,
    run_expired_tickets,
    run_expired_tickets_list,
    run_companies,
]


def run_all() -> None:
    for pipeline in PIPELINES:
        result = pipeline()
        print(result)


if __name__ == "__main__":
    run_all()
