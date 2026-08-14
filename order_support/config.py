"""Environment secrets and checked-in OpenRouter model configuration."""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_CONFIG_PATH = PROJECT_ROOT / "config" / "models.toml"
SUPPORTED_PROVIDER_FIELDS = {
    "allow_fallbacks",
    "data_collection",
    "ignore",
    "max_price",
    "only",
    "order",
    "preferred_max_latency",
    "preferred_min_throughput",
    "quantizations",
    "require_parameters",
    "sort",
    "zdr",
}


@dataclass(frozen=True)
class OpenRouterSettings:
    api_key: str
    base_url: str

    @classmethod
    def from_env(cls):
        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        base_url = os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ).strip()

        missing = [
            name
            for name, value in (
                ("OPENROUTER_API_KEY", api_key),
                ("OPENROUTER_BASE_URL", base_url),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "Missing required OpenRouter configuration: " + ", ".join(missing)
            )

        return cls(api_key=api_key, base_url=base_url)


@dataclass(frozen=True)
class ModelRoute:
    id: str
    label: str
    provider: dict


@dataclass(frozen=True)
class ModelOption:
    id: str
    label: str
    slug: str
    default_route: str
    routes: tuple[ModelRoute, ...]

    def resolve_route(self, route_id: str | None = None):
        selected_id = self.default_route if route_id is None else route_id
        for route in self.routes:
            if route.id == selected_id:
                return route
        raise ValueError(f"Unknown route {selected_id!r} for model {self.id!r}")


@dataclass(frozen=True)
class ModelCatalog:
    default_model: str
    models: tuple[ModelOption, ...]

    def resolve(self, model_id: str | None = None, route_id: str | None = None):
        selected_id = self.default_model if model_id is None else model_id
        for model in self.models:
            if model.id == selected_id:
                return model, model.resolve_route(route_id)
        raise ValueError(f"Unknown model {selected_id!r}")


def _required_string(mapping, key, location):
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location}.{key} must be a non-empty string")
    return value.strip()


def _validate_provider(provider, location):
    if not isinstance(provider, dict):
        raise ValueError(f"{location}.provider must be a table")
    unknown = sorted(set(provider) - SUPPORTED_PROVIDER_FIELDS)
    if unknown:
        raise ValueError(
            f"{location}.provider contains unsupported fields: {', '.join(unknown)}"
        )
    for key in ("ignore", "only", "order", "quantizations"):
        if key not in provider:
            continue
        value = provider[key]
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise ValueError(f"{location}.provider.{key} must be a list of strings")
    for key in ("allow_fallbacks", "require_parameters", "zdr"):
        if key in provider and not isinstance(provider[key], bool):
            raise ValueError(f"{location}.provider.{key} must be a boolean")
    if "data_collection" in provider and provider["data_collection"] not in {
        "allow",
        "deny",
    }:
        raise ValueError(
            f"{location}.provider.data_collection must be 'allow' or 'deny'"
        )
    return dict(provider)


def load_model_catalog(config_path: Path = DEFAULT_MODEL_CONFIG_PATH):
    config_path = Path(config_path)
    try:
        document = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Could not load model configuration: {config_path}") from error

    default_model = _required_string(document, "default_model", "models")
    raw_models = document.get("models")
    if not isinstance(raw_models, list) or not raw_models:
        raise ValueError("models must contain at least one model")

    models = []
    model_ids = set()
    for model_index, raw_model in enumerate(raw_models):
        location = f"models[{model_index}]"
        if not isinstance(raw_model, dict):
            raise ValueError(f"{location} must be a table")
        model_id = _required_string(raw_model, "id", location)
        if model_id in model_ids:
            raise ValueError(f"Duplicate model id: {model_id}")
        model_ids.add(model_id)

        raw_routes = raw_model.get("routes")
        if not isinstance(raw_routes, list) or not raw_routes:
            raise ValueError(f"{location}.routes must contain at least one route")
        routes = []
        route_ids = set()
        for route_index, raw_route in enumerate(raw_routes):
            route_location = f"{location}.routes[{route_index}]"
            if not isinstance(raw_route, dict):
                raise ValueError(f"{route_location} must be a table")
            route_id = _required_string(raw_route, "id", route_location)
            if route_id in route_ids:
                raise ValueError(f"Duplicate route id {route_id!r} for model {model_id!r}")
            route_ids.add(route_id)
            routes.append(
                ModelRoute(
                    id=route_id,
                    label=_required_string(raw_route, "label", route_location),
                    provider=_validate_provider(
                        raw_route.get("provider", {}),
                        route_location,
                    ),
                )
            )

        default_route = _required_string(raw_model, "default_route", location)
        if default_route not in route_ids:
            raise ValueError(
                f"Default route {default_route!r} is not defined for model {model_id!r}"
            )
        models.append(
            ModelOption(
                id=model_id,
                label=_required_string(raw_model, "label", location),
                slug=_required_string(raw_model, "slug", location),
                default_route=default_route,
                routes=tuple(routes),
            )
        )

    if default_model not in model_ids:
        raise ValueError(f"Default model {default_model!r} is not defined")
    return ModelCatalog(default_model=default_model, models=tuple(models))
