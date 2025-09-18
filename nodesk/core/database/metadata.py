import inspect
import pkgutil
from importlib import import_module

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.schema import MetaData


def get_metadata(
    base_package: str = "nodesk",
    exclude_prefixes: tuple[str, ...] = (
        "nodesk.core",
        "nodesk.__pycache__",
    ),
) -> list[MetaData]:
    seen: set[int] = set()
    metadata_list: list[MetaData] = []

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
            md_id = id(md)
            if md_id not in seen:
                metadata_list.append(md)
                seen.add(md_id)

    return metadata_list
