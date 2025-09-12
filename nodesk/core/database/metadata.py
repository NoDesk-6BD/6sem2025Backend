import inspect
import pkgutil
from collections.abc import Iterator
from importlib import import_module
from types import ModuleType

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.schema import MetaData


def provide_metadata(
    base_package: str = "nodesk",
    exclude_prefixes: tuple[str, ...] = (
        "nodesk.core",
        "nodesk.__pycache__",
    ),
) -> list[MetaData]:
    """
    Recursively import modules under `base_package`, find classes that look like
    ORM models (structurally: have __tablename__), confirm they are actually
    mapped via SQLAlchemy, and collect their registries' MetaData.
    Returns a deduplicated list of MetaData objects (Alembic accepts a list).
    """
    metas: list[MetaData] = []
    seen: set[int] = set()

    pkg = import_module(base_package)
    for info in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        name = info.name
        if any(name.startswith(p) for p in exclude_prefixes):
            continue
        try:
            mod = import_module(name)
        except Exception:
            continue

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if getattr(obj, "__module__", None) != mod.__name__:
                continue
            if not hasattr(obj, "__tablename__"):
                continue
            try:
                mapper = sa_inspect(obj)
            except NoInspectionAvailable:
                continue
            md = mapper.registry.metadata
            if id(md) not in seen:
                metas.append(md)
                seen.add(id(md))

    return metas
