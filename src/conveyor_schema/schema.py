import typing as t

import attr


@attr.dataclass(slots=True, kw_only=True)
class Schema:
    models: dict[str, "Model"]

    def get_model(self, model_name: str) -> "ModelManager":
        return self.models[model_name]._make_manager(self)


@attr.dataclass(slots=True, kw_only=True)
class Model:
    name: str
    label: str
    label_plural: str
    display_field: str = "display_value"

    def _make_manager(self, schema: Schema) -> "ModelManager":
        return ModelManager(schema, self)


class ModelManager:
    def __init__(self, schema: Schema, model: Model) -> None:
        self._schema = schema
        self._model = model

    def label(self, item: t.Any, items: list[t.Any]) -> str:
        return self._model.label

    def label_plural(self, item: t.Any, items: list[t.Any]) -> str:
        return self._model.label_plural

    def display_value(self, item: t.Any) -> str:
        return str(getattr(item, self._model.display_field, ""))
