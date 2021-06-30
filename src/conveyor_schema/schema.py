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
    """Top-level schema object containing the models and other
    application-level information.
    """

    models: dict[str, Model] = attr.ib(converter=_list_to_index)
    """Map of model names to :class:`Model` instances."""

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
    """Describes a single model in the schema. A model has various views
    such as index, detail, create, and check delete, which the schema
    describes. The fields of a model can be attributes as well as
    relationships to other models.
    """

    _schema: Schema = attr.ib(init=False)
    """The top-level :class:`Schema`."""

    name: str
    """The internal name of the model. Used as the key in
    :attr:`Schema.models` and URLs.
    """
    label: str = attr.ib(default=_to_title("name"))
    """The user-facing name of the model. Defaults to the :attr:`name`
    split on ``_`` and in title case.
    """
    label_plural: str = attr.ib(default=_to_plural("label"))
    """The user-facing plural name of the model. Defaults to an
    attempt to pluralize :attr:`label`.
    """
    fields: dict[str, Field] = attr.ib(converter=_list_to_index)
    """Map of field names to :class:`Field` instances."""
    field_order: list[str] = attr.ib(default=_to_list("fields"))
    """Field names in the order they should be displayed if not
    overridden by a more specific attribute. Defaults to the insertion
    order of :attr:`fields`.
    """
    display_field: str = "name"
    """The field to access on an instance of the model that has a
    value to display for the instance. Used by
    :meth:`get_display_value`.
    """
    is_singleton: bool = False
    """A singleton model cannot be created or deleted. In a UI, it
    would have a single URL instead of index and detail pages.
    """
    has_index: bool = True
    """Whether an index page should be shown."""
    index_field_order: typing.Optional[list[str]] = None
    """The fields to display as columns on the index page, in order.
    Used by :meth:`get_index_field_order`.
    """
    table_link_field: str = attr.ib(default=_value_of("display_field"))
    """The field to use as a link to the detail page in a table.
    Defaults to the same field as :attr:`display_field`."""
    table_can_sort: bool = True
    """Whether the table can be sorted."""
    table_can_filter: bool = True
    """Whether the table can be filtered."""
    table_can_page: bool = True
    """Whether the table should be shown in multiple pages if there are
    too many rows.
    """
    has_create: bool = True
    """Whether instances can be created."""
    create_field_order: typing.Optional[list[str]] = None
    """The fields to display as inputs on the create page, in order.
    Used by :meth:`get_create_field_order`.
    """
    has_delete: bool = True
    """Whether instances can be deleted."""
    show_in_rel_delete: bool = True
    """Whether this model should be shown when checking if it is safe to
    delete a related model.
    """
    has_detail: bool = True
    """Whether a detail page should be shown."""
    show_in_search: bool = attr.ib(default=_value_of("has_detail"))
    """Whether instances of this model should show up in search."""
    detail_tabs: typing.Optional[list[DetailTab]] = None
    """The detail page can be organized into tabs that each show a
    subset of the fields.
    """
    detail_field_order: typing.Optional[list[str]] = None
    """The fields to display on the detail page, in order. Used by
    :meth:`get_detail_field_order`.
    """
    tooltip_field_order: typing.Optional[list[str]] = None
    """The fields to display in link tooltips, in order. Used by
    :meth:`get_tooltip_field_order`.
    """
    query_list: str = attr.ib(default=_to_lower_camel("label_plural"))
    """The name of the query to get a list of instances of this model."""
    query_single: str = attr.ib(default=_to_lower_camel("label"))
    """The name of the query to get a single instance of this model."""
    query_required_fields: list[str] = attr.ib(default=_default_query_required_fields)
    """Fields to always include in any queries."""

    def get_display_value(self, obj: typing.Any) -> str:
        """The value to display for a given instance of the model. By
        default this is the value of the attribute named by
        :attr:`display_field`.

        :param obj: An instance of the model.
        """
        return str(getattr(obj, self.display_field))

    def _get_field_order(
        self: Model, where: str, query: typing.Optional[str] = None
    ) -> list[str]:
        """Build a field order.

        :param where: The name of the ``_field_order`` and ``show_``
            attributes to use.
        :param query: Use ``query_`` attributes with this name.
        """
        if query is None:
            out = []
        else:
            out = self.query_required_fields.copy()

        required = set(out)
        order = getattr(self, f"{where}_field_order")

        if order is not None:
            out.extend(name for name in order if name not in required)
            return out

        for name in self.field_order:
            if name in required:
                continue

            field = self.fields[name]
            show = getattr(field, f"show_{where}")

            if query is None:
                if show:
                    out.append(name)
            elif not field.virtual and (
                show or getattr(field, f"query_{query}_include")
            ):
                out.append(name)

        return out

    def get_index_field_order(self) -> list[str]:
        """The fields to display as columns on the index page, in order.
        By default this uses :attr:`index_field_order` if that is set,
        or each field in :attr:`field_order` with
        :attr:`Field.show_index` enabled.
        """
        return self._get_field_order("index")

    def get_create_field_order(self) -> list[str]:
        """The fields to display as inputs on the create page, in order.
        By default this uses :attr:`create_field_order` if that is set,
        or each field in :attr:`field_order` with
        :attr:`Field.show_create` enabled.
        """
        return self._get_field_order("create")

    def get_detail_field_order(self) -> list[str]:
        """The fields to display on the detail page, in order. By
        default this uses:

        -   The order of attributes in all :attr:`detail_tabs`, if set.
        -   :attr:`detail_field_order`, if set.
        -   Each field in :attr:`field_order` with
            :attr:`Field.show_detail` enabled.
        """
        if self.detail_tabs is not None:
            out = []

            for tab in self.detail_tabs:
                out.extend(tab._flatten_fields())

            return out

        return self._get_field_order("detail")

    def get_tooltip_field_order(self) -> list[str]:
        """The fields to display in link tooltips, in order. By default
        this uses :attr:`tooltip_field_order` if that is set, or each
        field in :attr:`field_order` with :attr:`Field.show_tooltip`
        enabled.
        """
        return self._get_field_order("tooltip")

    def get_query_list_fields(self) -> list[str]:
        """The fields to request in the list query. By default this uses
        :attr:`index_field_order` if that is set, or each field in
        :attr:`field_order` with :attr:`Field.show_index` or
        :attr:`query_list_include` enabled that is not marked
        :attr:`Field.virtual`. Fields in :attr:`query_required_fields`
        are always included.
        """
        return self._get_field_order("index", query="list")

    def get_query_single_fields(self) -> list[str]:
        """The fields to request in the single query. By default this
        uses :attr:`detail_field_order` if that is set, or each field in
        :attr:`field_order` with :attr:`Field.show_detail` or
        :attr:`query_single_include` enabled that is not marked
        :attr:`Field.virtual`. Fields in :attr:`query_required_fields`
        are always included.
        """
        return self._get_field_order("detail", query="single")


@attr.s(repr=False, eq=False, order=False, slots=True, kw_only=True, auto_attribs=True)
class DetailTab:
    """A tab on the detail page. Can show a subset of the model's fields
    as well as nested tabs.

    Not required to show fields or tabs. If :attr:`fields` and
    :attr:`tabs` are left empty it specifies a named tab that will have
    custom behavior in the UI.
    """

    name: str
    """The internal name of the tab. Used in URLs."""
    label: str = attr.ib(default=_to_title("name"))
    """The user-facing name of the tab. Defaults to the :attr:`name`
    split on ``_`` and in title case.
    """
    fields: list[str]
    """The fields to display on the tab, in order."""
    tabs: typing.Optional[list[DetailTab]] = None
    """Sub-tabs to show under this tab. Typically shown under any fields
    in the tab.
    """

    def _flatten_fields(self) -> list[str]:
        out = self.fields.copy()

        if self.tabs is not None:
            for tab in self.tabs:
                out.extend(tab._flatten_fields())

        return out


class _NameEnum(enum.Enum):
    """An enum where each member's value matches its name."""

    def _generate_next_value_(self: str, *args) -> str:  # type: ignore
        return self

    def __repr__(self) -> str:
        return f"<{type(self).__name__}.{self.name}>"


class FieldType(_NameEnum):
    """Built-in input types understood by Autoinvent."""

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
    """Describes a single field in a model. A field is present as data
    or an input in a UI. Its attributes describe how it behaves when
    viewing, editing, and querying it.
    """

    _schema: Schema = attr.ib(init=False)
    """The top-level :class:`Schema`."""
    _model: Model = attr.ib(init=False)
    """The :class:`Model` this field is part of."""

    name: str
    """The internal name of the field. Used as the key in
    :attr:`Model.fields`.
    """
    type: typing.Union[str, RelationshipInfo] = attr.ib(
        default="string", converter=_convert_type
    )
    """The type of data this field represents. Can affect how the data
    is displayed, validated, etc. A value from :class:`FieldType`
    describes a basic type, or a string can be given for a custom type.
    A :class:`RelationshipInfo` describes extra information about a
    relationship to another model. Defaults to ``"string"``.
    """
    is_attribute: bool = attr.ib(default=_is_attribute)
    """Whether this field should be treated as a key/value attribute or
    as a relationship table. Basic types default to ``True``,
    relationship types default to ``False`` if they are in the "to one"
    direction.
    """
    choices: typing.Optional[list[tuple[str, str]]] = attr.ib(
        default=None, converter=_convert_choices
    )
    """A list of ``(value, label)`` tuples. If given, only these values
    are allowed for the field. As a shortcut, a list of strings can be
    passed if the value and label should be the same, or a dict mapping
    values to labels.
    """
    label: str = attr.ib(default=_to_title("name"))
    """The user-facing name of the field. Defaults to the :attr:`name`
    split on ``_`` and in title case.
    """
    label_help: typing.Optional[str] = None
    """Info to display to the user describing the field. The UI might
    show this from an information icon next to the label.
    """
    no_data_value: typing.Optional[str] = "N/A"
    """What to display if the field's value is ``None``. Use ``None`` to
    display empty space. Defaults to "N/A".
    """
    input_help: typing.Optional[str] = None
    """Info to display to the user describing the value being input. The
    UI might show this under an input when creating or editing.
    """
    is_disabled: bool = False
    """The input is visible but disabled."""
    can_sort: bool = True
    """When displayed in a table, this column can be sorted."""
    can_filter: bool = True
    """When displayed in a table, this field can be filtered on."""
    can_edit: bool = True
    """This field can be edited."""
    can_collapse: bool = True
    """When shown as a table (:attr:`is_attribute` is ``False``), allow
    collapsing / hiding / minimizing the table.
    """
    show_index: bool = True
    """Show this field on the index page (and other tables). Only used
    if :attr:`Model.index_field_order` is not set.
    """
    show_create: bool = True
    """Show this field on the create page. Only used if
    :attr:`Model.create_field_order` is not set.
    """
    show_detail: bool = True
    """Show this field on the detail page (and other tables). Only used
    if :attr:`Model.detail_field_order` is not set.
    """
    show_tooltip: bool = False
    """Show this field in tooltips. Only used if
    :attr:`Model.tooltip_field_order` is not set.
    """
    query_list_include: bool = True
    """Request this field when querying for a list of items."""
    query_single_include: bool = True
    """Request this field when querying for a single item."""
    virtual: bool = False
    """A field that is not present in data or queries. It is a
    placeholder for custom local behavior.
    """


class RelationshipType(_NameEnum):
    """Indicates the amount and direction of the relationship between
    two models.
    """

    many_to_one = enum.auto()
    one_to_many = enum.auto()
    many_to_many = enum.auto()
    one_to_one = enum.auto()


@attr.s(repr=False, eq=False, order=False, slots=True, kw_only=True, auto_attribs=True)
class RelationshipInfo:
    _schema: Schema = attr.ib(init=False)
    """The top-level :class:`Schema`."""
    _model: Model = attr.ib(init=False)
    """The :class:`Model` the field with this type is part of."""
    _field: Field = attr.ib(init=False)
    """The :class:`Field` with this type."""

    type: RelationshipType
    """A value from :class:`RelationshipType` describing the size and
    direction of the relationship.
    """
    target: str
    """The name of the model this relationship is pointing to."""
    backref: typing.Optional[str]
    """The name of the field on the target model that points to this
    model. Used to keep data in sync.
    """
    table_field_order: typing.Optional[list[str]] = None
    """The fields of the :attr:`target` model to display as columns on
    the source model's detail page table, in order. Used by
    :meth:`get_table_field_order`.
    """

    def get_table_field_order(self) -> list[str]:
        """The fields of the :attr:`target` model to display as columns
        on the source model's detail page table, in order. By default
        this uses :attr:`table_field_order` if that is set, or calls
        :meth:`Model.get_index_field_order` for the target.
        """
        if self.table_field_order is not None:
            return self.table_field_order

        return self._schema.models[self.target].get_index_field_order()
