from __future__ import annotations

import enum
import typing
from functools import wraps

import attr
import inflect

_p = inflect.engine()

_V = typing.TypeVar("_V")


def _list_to_index(
    value: typing.Union[dict[str, typing.Any], list[typing.Any]]
) -> dict[str, typing.Any]:
    if isinstance(value, dict):
        return value

    return {field.name: field for field in value}


@attr.s(repr=False, eq=False, order=False, slots=True, kw_only=True, auto_attribs=True)
class Schema:
    models: dict[str, Model] = attr.ib(converter=_list_to_index)

    def __attrs_post_init__(self) -> None:
        for model in self.models.values():
            model._schema = self

            for field in model.fields.values():
                field._schema = self
                field._model = model

                if isinstance(field.type, RelationshipInfo):
                    field.type._schema = self
                    field.type._model = model
                    field.type._field = field


def _self_processor(f: typing.Callable[[typing.Any], _V]) -> _V:
    return attr.Factory(f, takes_self=True)


def _attr_processor(f: typing.Callable[[typing.Any], _V]) -> typing.Callable[[str], _V]:
    @wraps(f)
    def make_processor(name: str) -> _V:
        @_self_processor
        def processor(self: typing.Any) -> _V:
            value = getattr(self, name)
            return f(value)

        return processor

    return make_processor


@_attr_processor
def _to_title(value: str) -> str:
    return value.replace("_", " ").title()


@_attr_processor
def _to_plural(value: str) -> str:
    return _p.plural_noun(value)  # type: ignore[no-any-return]


@_attr_processor
def _to_lower_camel(value: str) -> str:
    words = value.split()
    words[0] = words[0].lower()
    return "".join(words)


@_attr_processor
def _value_of(value: typing.Any) -> typing.Any:
    return value


@_attr_processor
def _to_list(value: typing.Any) -> list[typing.Any]:
    return list(value)


@_self_processor
def _default_query_required_fields(self: Model) -> list[str]:
    return ["id", self.display_field]


@attr.s(repr=False, eq=False, order=False, slots=True, kw_only=True, auto_attribs=True)
class Model:
    _schema: Schema = attr.ib(init=False)

    name: str
    label: str = attr.ib(default=_to_title("name"))
    label_plural: str = attr.ib(default=_to_plural("label"))
    fields: dict[str, Field] = attr.ib(converter=_list_to_index)
    field_order: list[str] = attr.ib(default=_to_list("fields"))
    display_field: str = "name"
    is_singleton: bool = False
    has_index: bool = True
    index_field_order: typing.Optional[list[str]] = None
    table_link_field: str = attr.ib(default=_value_of("display_field"))
    table_can_sort: bool = True
    table_can_filter: bool = True
    table_can_page: bool = True
    has_create: bool = True
    create_field_order: typing.Optional[list[str]] = None
    has_delete: bool = True
    show_in_rel_delete: bool = True
    has_detail: bool = True
    show_in_search: bool = attr.ib(default=_value_of("has_detail"))
    detail_tabs: typing.Optional[list[DetailTab]] = None
    detail_field_order: typing.Optional[list[str]] = None
    tooltip_field_order: typing.Optional[list[str]] = None
    query_list: str = attr.ib(default=_to_lower_camel("label_plural"))
    query_item: str = attr.ib(default=_to_lower_camel("label"))
    query_required_fields: list[str] = attr.ib(default=_default_query_required_fields)

    def get_display_value(self, item: typing.Any) -> str:
        return str(getattr(item, self.display_field))

    def _get_field_order(
        self: Model, where: str, query: typing.Optional[str] = None
    ) -> list[str]:
        if getattr(self, f"{where}_field_order") is not None:
            return getattr(self, f"{where}_field_order")  # type: ignore[no-any-return]

        if query is None:
            out = []
        else:
            out = self.query_required_fields.copy()

        required = set(out)

        for name in self.field_order:
            if name in required:
                continue

            field = self.fields[name]
            show = getattr(field, f"show_{where}")

            if query is None:
                if show:
                    out.append(name)
            elif not field.ui_only and (show or getattr(field, f"query_{query}")):
                out.append(name)

        return out

    def get_index_field_order(self) -> list[str]:
        return self._get_field_order("index")

    def get_create_field_order(self) -> list[str]:
        return self._get_field_order("create")

    def get_detail_field_order(self) -> list[str]:
        if self.detail_tabs is not None:
            out = []

            for tab in self.detail_tabs:
                out.extend(tab._flatten_fields())

            return out

        return self._get_field_order("detail")

    def get_tooltip_field_order(self) -> list[str]:
        return self._get_field_order("tooltip")

    def get_query_list_fields(self) -> list[str]:
        return self._get_field_order("index", query="list")

    def get_query_item_fields(self) -> list[str]:
        return self._get_field_order("detail", query="item")


@attr.s(repr=False, eq=False, order=False, slots=True, kw_only=True, auto_attribs=True)
class DetailTab:
    name: str
    label: str = attr.ib(default=_to_title("name"))
    fields: list[str]
    tabs: typing.Optional[list[DetailTab]] = None

    def _flatten_fields(self) -> list[str]:
        out = self.fields.copy()

        if self.tabs is not None:
            for tab in self.tabs:
                out.extend(tab._flatten_fields())

        return out


class _NameEnum(enum.Enum):
    def _generate_next_value_(self: str, *args) -> str:  # type: ignore
        return self

    def __repr__(self) -> str:
        return f"<{type(self).__name__}.{self.name}>"


class FieldType(_NameEnum):
    string = enum.auto()
    textarea = enum.auto()
    password = enum.auto()
    integer = enum.auto()
    float = enum.auto()
    date_time = enum.auto()
    date = enum.auto()
    color = enum.auto()
    url = enum.auto()
    email = enum.auto()
    phone = enum.auto()
    currency = enum.auto()
    file = enum.auto()
    boolean = enum.auto()
    radio = enum.auto()
    checkbox = enum.auto()
    creatable_select = enum.auto()
    id = enum.auto()


def _convert_type(
    value: typing.Union[FieldType, str, RelationshipInfo]
) -> typing.Union[str, RelationshipInfo]:
    if isinstance(value, FieldType):
        return value.value

    return value


def _convert_choices(
    data: typing.Optional[
        typing.Union[list[typing.Union[str, tuple[str, str]]], dict[str, str]]
    ]
) -> typing.Optional[list[tuple[str, str]]]:
    if data is None:
        return data

    if isinstance(data, dict):
        return list(data.items())

    out = []

    for item in data:
        if isinstance(item, str):
            out.append((item, item))
        else:
            out.append(item)

    return out


@_self_processor
def _is_attribute(self: Field) -> bool:
    if isinstance(self.type, str):
        return True

    return self.type.type in {RelationshipType.many_to_one, RelationshipType.one_to_one}


@attr.s(repr=False, eq=False, order=False, slots=True, kw_only=True, auto_attribs=True)
class Field:
    _schema: Schema = attr.ib(init=False)
    _model: Model = attr.ib(init=False)

    name: str
    type: typing.Union[str, RelationshipInfo] = attr.ib(
        default="string", converter=_convert_type
    )
    is_attribute: bool = attr.ib(default=_is_attribute)
    choices: typing.Optional[list[tuple[str, str]]] = attr.ib(
        default=None, converter=_convert_choices
    )
    label: str = attr.ib(default=_to_title("name"))
    label_help: typing.Optional[str] = None
    no_data_value: str = "N/A"
    input_help: typing.Optional[str] = None
    is_disabled: bool = False
    can_sort: bool = True
    can_filter: bool = True
    can_edit: bool = True
    can_collapse: bool = True
    show_index: bool = True
    show_create: bool = True
    show_detail: bool = True
    show_tooltip: bool = False
    query_list_include: bool = True
    query_item_include: bool = True
    ui_only: bool = False


class RelationshipType(_NameEnum):
    many_to_one = enum.auto()
    one_to_many = enum.auto()
    many_to_many = enum.auto()
    one_to_one = enum.auto()


@attr.s(repr=False, eq=False, order=False, slots=True, kw_only=True, auto_attribs=True)
class RelationshipInfo:
    _schema: Schema = attr.ib(init=False)
    _model: Model = attr.ib(init=False)
    _field: Field = attr.ib(init=False)

    type: RelationshipType
    target: str
    backref: str
    table_field_order: typing.Optional[list[str]] = None

    def get_table_field_order(self) -> list[str]:
        if self.table_field_order is not None:
            return self.table_field_order

        return self._schema.models[self.target].get_index_field_order()
