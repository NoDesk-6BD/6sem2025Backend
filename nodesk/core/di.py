import inspect
from collections.abc import Callable
from typing import Any

# One placeholder provider per token (class, Protocol, etc.)
_PROVIDER_REGISTRY: dict[Any, Callable[..., Any]] = {}


def _token_name(token: Any) -> str:
    name = getattr(token, "__name__", None) or getattr(token, "__qualname__", None)
    if not name:
        name = repr(token)
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)


def provider_for(token: Any) -> Callable[..., Any]:
    """
    Return a stable callable to use in Depends(...) and as the key for
    app.dependency_overrides. By default it raises until bound.
    """
    if token in _PROVIDER_REGISTRY:
        return _PROVIDER_REGISTRY[token]

    async def _missing_dependency(*_args: Any, **_kwargs: Any) -> Any:  # noqa: ANN401
        raise RuntimeError(f"Dependency not bound: {token!r}.")

    _missing_dependency.__name__ = f"provide_{_token_name(token)}"
    # Ensure FastAPI sees a zero-parameter signature
    _missing_dependency.__signature__ = inspect.Signature(parameters=())  # type: ignore[attr-defined]
    _PROVIDER_REGISTRY[token] = _missing_dependency
    return _PROVIDER_REGISTRY[token]
