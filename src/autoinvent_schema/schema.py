from __future__ import annotations

import enum
import typing as t

import inflect

_p = inflect.engine()


def _to_title(value: str) -> str:
    return value.replace("_", " ").title()


def _to_lower_camel(value: str) -> str:
    words = value.split()
    words[0] = words[0].lower()
    return "".join(words)


class Schema:
    """Top-level schema object containing the models and other
    application-level information.
    """

    models: dict[str, Model]
    """Map of model names to :class:`Model` instances."""

    def __init__(self, *, models: t.Union[dict[str, Model], list[Model]]) -> None:
        if isinstance(models, list):
            models = {m.name: m for m in models}

        self.models = models

        for model in self.models.values():
            model._schema = self

            for field in model.fields.values():
                field._schema = self
                field._model = model

                if isinstance(field.type, RelationshipInfo):
                    field.type._schema = self
                    field.type._model = model
                    field.type._field = field


class Model:
    """Describes a single model in the schema. A model has various views
    such as index, detail, create, and check delete, which the schema
    describes. The fields of a model can be attributes as well as
    relationships to other models.
    """

    _schema: Schema
    """The top-level :class:`Schema`."""

    name: str
    """The internal name of the model. Used as the key in
    :attr:`Schema.models` and URLs.
    """
    label: str
    """The user-facing name of the model. Defaults to the :attr:`name`
    split on ``_`` and in title case.
    """
    label_plural: str
    """The user-facing plural name of the model. Defaults to an
    attempt to pluralize :attr:`label`.
    """
    fields: dict[str, Field]
    """Map of field names to :class:`Field` instances."""
    field_order: list[str]
    """Field names in the order they should be displayed if not
    overridden by a more specific attribute. Defaults to the insertion
    order of :attr:`fields`.
    """
    display_field: str
    """The field to access on an instance of the model that has a
    value to display for the instance. Used by
    :meth:`get_display_value`.
    """
    is_singleton: bool
    """A singleton model cannot be created or deleted. In a UI, it
    would have a single URL instead of index and detail pages.
    """
    has_index: bool
    """Whether an index page should be shown."""
    index_field_order: t.Optional[list[str]]
    """The fields to display as columns on the index page, in order.
    Used by :meth:`get_index_field_order`.
    """
    table_link_field: str
    """The field to use as a link to the detail page in a table.
    Defaults to the same field as :attr:`display_field`."""
    table_can_sort: bool
    """Whether the table can be sorted."""
    table_can_filter: bool
    """Whether the table can be filtered."""
    table_can_page: bool
    """Whether the table should be shown in multiple pages if there are
    too many rows.
    """
    has_create: bool
    """Whether instances can be created."""
    create_field_order: t.Optional[list[str]]
    """The fields to display as inputs on the create page, in order.
    Used by :meth:`get_create_field_order`.
    """
    has_delete: bool
    """Whether instances can be deleted."""
    show_in_rel_delete: bool
    """Whether this model should be shown when checking if it is safe to
    delete a related model.
    """
    has_detail: bool
    """Whether a detail page should be shown."""
    show_in_search: bool
    """Whether instances of this model should show up in search."""
    detail_tabs: t.Optional[list[DetailTab]]
    """The detail page can be organized into tabs that each show a
    subset of the fields.
    """
    detail_field_order: t.Optional[list[str]]
    """The fields to display on the detail page, in order. Used by
    :meth:`get_detail_field_order`.
    """
    tooltip_field_order: t.Optional[list[str]]
    """The fields to display in link tooltips, in order. Used by
    :meth:`get_tooltip_field_order`.
    """
    query_list: str
    """The name of the query to get a list of instances of this model."""
    query_single: str
    """The name of the query to get a single instance of this model."""
    query_required_fields: list[str]
    """Fields to always include in any queries."""

    def __init__(
        self,
        *,
        name: str,
        label: t.Optional[str] = None,
        label_plural: t.Optional[str] = None,
        fields: t.Union[dict[str, Field], list[Field]],
        field_order: t.Optional[list[str]] = None,
        display_field: str = "name",
        is_singleton: bool = False,
        has_index: bool = True,
        index_field_order: t.Optional[list[str]] = None,
        table_link_field: t.Optional[str] = None,
        table_can_sort: bool = True,
        table_can_filter: bool = True,
        table_can_page: bool = True,
        has_create: bool = True,
        create_field_order: t.Optional[list[str]] = None,
        has_delete: bool = True,
        show_in_rel_delete: bool = True,
        has_detail: bool = True,
        show_in_search: t.Optional[bool] = None,
        detail_tabs: t.Optional[list[DetailTab]] = None,
        detail_field_order: t.Optional[list[str]] = None,
        tooltip_field_order: t.Optional[list[str]] = None,
        query_list: t.Optional[str] = None,
        query_single: t.Optional[str] = None,
        query_required_fields: t.Optional[list[str]] = None,
    ) -> None:
        self.name = name

        if label is None:
            label = _to_title(self.name)

        self.label = label

        if label_plural is None:
            label_plural = _p.plural_noun(self.label)

        self.label_plural = label_plural

        if isinstance(fields, list):
            fields = {f.name: f for f in fields}

        self.fields = fields

        if field_order is None:
            field_order = list(self.fields)

        self.field_order = field_order
        self.display_field = display_field
        self.is_singleton = is_singleton
        self.has_index = has_index
        self.index_field_order = index_field_order

        if table_link_field is None:
            table_link_field = self.display_field

        self.table_link_field = table_link_field
        self.table_can_sort = table_can_sort
        self.table_can_filter = table_can_filter
        self.table_can_page = table_can_page
        self.has_create = has_create
        self.create_field_order = create_field_order
        self.has_delete = has_delete
        self.show_in_rel_delete = show_in_rel_delete
        self.has_detail = has_detail

        if show_in_search is None:
            show_in_search = self.has_detail

        self.show_in_search = show_in_search
        self.detail_tabs = detail_tabs
        self.detail_field_order = detail_field_order
        self.tooltip_field_order = tooltip_field_order

        if query_list is None:
            query_list = _to_lower_camel(self.label_plural)

        self.query_list = query_list

        if query_single is None:
            query_single = _to_lower_camel(self.label)

        self.query_single = query_single

        if query_required_fields is None:
            query_required_fields = ["id", self.display_field]

        self.query_required_fields = query_required_fields

    def get_display_value(self, obj: t.Any) -> str:
        """The value to display for a given instance of the model. By
        default this is the value of the attribute named by
        :attr:`display_field`.

        :param obj: An instance of the model.
        """
        return str(getattr(obj, self.display_field))

    def _get_field_order(
        self: Model, where: str, query: t.Optional[str] = None
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


class DetailTab:
    """A tab on the detail page. Can show a subset of the model's fields
    as well as nested tabs.

    Not required to show fields or tabs. If :attr:`fields` and
    :attr:`tabs` are left empty it specifies a named tab that will have
    custom behavior in the UI.
    """

    name: str
    """The internal name of the tab. Used in URLs."""
    label: str
    """The user-facing name of the tab. Defaults to the :attr:`name`
    split on ``_`` and in title case.
    """
    fields: list[str]
    """The fields to display on the tab, in order."""
    tabs: t.Optional[list[DetailTab]]
    """Sub-tabs to show under this tab. Typically shown under any fields
    in the tab.
    """

    def __init__(
        self,
        *,
        name: str,
        label: t.Optional[str] = None,
        fields: list[str],
        tabs: t.Optional[list[DetailTab]] = None,
    ) -> None:
        self.name = name

        if label is None:
            label = _to_title(self.name)

        self.label = label
        self.fields = fields
        self.tabs = tabs

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


class Field:
    """Describes a single field in a model. A field is present as data
    or an input in a UI. Its attributes describe how it behaves when
    viewing, editing, and querying it.
    """

    _schema: Schema
    """The top-level :class:`Schema`."""
    _model: Model
    """The :class:`Model` this field is part of."""

    name: str
    """The internal name of the field. Used as the key in
    :attr:`Model.fields`.
    """
    type: t.Union[str, RelationshipInfo]
    """The type of data this field represents. Can affect how the data
    is displayed, validated, etc. A value from :class:`FieldType`
    describes a basic type, or a string can be given for a custom type.
    A :class:`RelationshipInfo` describes extra information about a
    relationship to another model. Defaults to ``"string"``.
    """
    is_attribute: bool
    """Whether this field should be treated as a key/value attribute or
    as a relationship table. Basic types default to ``True``,
    relationship types default to ``False`` if they are in the "to one"
    direction.
    """
    choices: t.Optional[list[tuple[str, str]]]
    """A list of ``(value, label)`` tuples. If given, only these values
    are allowed for the field. As a shortcut, a list of strings can be
    passed if the value and label should be the same, or a dict mapping
    values to labels.
    """
    label: str
    """The user-facing name of the field. Defaults to the :attr:`name`
    split on ``_`` and in title case.
    """
    label_help: t.Optional[str]
    """Info to display to the user describing the field. The UI might
    show this from an information icon next to the label.
    """
    no_data_value: t.Optional[str]
    """What to display if the field's value is ``None``. Use ``None`` to
    display empty space. Defaults to "N/A".
    """
    input_help: t.Optional[str]
    """Info to display to the user describing the value being input. The
    UI might show this under an input when creating or editing.
    """
    is_disabled: bool
    """The input is visible but disabled."""
    can_sort: bool
    """When displayed in a table, this column can be sorted."""
    can_filter: bool
    """When displayed in a table, this field can be filtered on."""
    can_edit: bool
    """This field can be edited."""
    can_collapse: bool
    """When shown as a table (:attr:`is_attribute` is ``False``), allow
    collapsing / hiding / minimizing the table.
    """
    show_index: bool
    """Show this field on the index page (and other tables). Only used
    if :attr:`Model.index_field_order` is not set.
    """
    show_create: bool
    """Show this field on the create page. Only used if
    :attr:`Model.create_field_order` is not set.
    """
    show_detail: bool
    """Show this field on the detail page (and other tables). Only used
    if :attr:`Model.detail_field_order` is not set.
    """
    show_tooltip: bool
    """Show this field in tooltips. Only used if
    :attr:`Model.tooltip_field_order` is not set.
    """
    query_list_include: bool
    """Request this field when querying for a list of items."""
    query_single_include: bool
    """Request this field when querying for a single item."""
    virtual: bool
    """A field that is not present in data or queries. It is a
    placeholder for custom local behavior.
    """

    def __init__(
        self,
        *,
        name: str,
        type: t.Union[FieldType, str, RelationshipInfo] = FieldType.string,
        is_attribute: t.Optional[bool] = None,
        choices: t.Optional[t.Union[list[tuple[str, str]], dict[str, str]]] = None,
        label: t.Optional[str] = None,
        label_help: t.Optional[str] = None,
        no_data_value: t.Optional[str] = "N/A",
        input_help: t.Optional[str] = None,
        is_disabled: bool = False,
        can_sort: bool = True,
        can_filter: bool = True,
        can_edit: bool = True,
        can_collapse: bool = True,
        show_index: bool = True,
        show_create: bool = True,
        show_detail: bool = True,
        show_tooltip: bool = False,
        query_list_include: bool = True,
        query_single_include: bool = True,
        virtual: bool = False,
    ) -> None:
        self.name = name

        if isinstance(type, FieldType):
            type = type.value

        self.type = type

        if is_attribute is None:
            is_attribute = isinstance(self.type, str) or self.type.type in {
                RelationshipType.many_to_one,
                RelationshipType.one_to_one,
            }

        self.is_attribute = is_attribute

        if isinstance(choices, dict):
            choices = list(choices.items())

        self.choices = choices

        if label is None:
            label = _to_title(self.name)

        self.label = label
        self.label_help = label_help
        self.no_data_value = no_data_value
        self.input_help = input_help
        self.is_disabled = is_disabled
        self.can_sort = can_sort
        self.can_filter = can_filter
        self.can_edit = can_edit
        self.can_collapse = can_collapse
        self.show_index = show_index
        self.show_create = show_create
        self.show_detail = show_detail
        self.show_tooltip = show_tooltip
        self.query_list_include = query_list_include
        self.query_single_include = query_single_include
        self.virtual = virtual


class RelationshipType(_NameEnum):
    """Indicates the amount and direction of the relationship between
    two models.
    """

    many_to_one = enum.auto()
    one_to_many = enum.auto()
    many_to_many = enum.auto()
    one_to_one = enum.auto()


class RelationshipInfo:
    _schema: Schema
    """The top-level :class:`Schema`."""
    _model: Model
    """The :class:`Model` the field with this type is part of."""
    _field: Field
    """The :class:`Field` with this type."""

    type: RelationshipType
    """A value from :class:`RelationshipType` describing the size and
    direction of the relationship.
    """
    target: str
    """The name of the model this relationship is pointing to."""
    backref: t.Optional[str]
    """The name of the field on the target model that points to this
    model. Used to keep data in sync.
    """
    table_field_order: t.Optional[list[str]]
    """The fields of the :attr:`target` model to display as columns on
    the source model's detail page table, in order. Used by
    :meth:`get_table_field_order`.
    """

    def __init__(
        self,
        *,
        type: RelationshipType,
        target: str,
        backref: t.Optional[str] = None,
        table_field_order: t.Optional[list[str]] = None,
    ) -> None:
        self.type = type
        self.target = target
        self.backref = backref
        self.table_field_order = table_field_order

    def get_table_field_order(self) -> list[str]:
        """The fields of the :attr:`target` model to display as columns
        on the source model's detail page table, in order. By default
        this uses :attr:`table_field_order` if that is set, or calls
        :meth:`Model.get_index_field_order` for the target.
        """
        if self.table_field_order is not None:
            return self.table_field_order

        return self._schema.models[self.target].get_index_field_order()
