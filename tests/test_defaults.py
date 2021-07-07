from autoinvent_schema.schema import Field
from autoinvent_schema.schema import Model
from autoinvent_schema.schema import Schema

model = Model(
    name="user",
    fields={
        "id": Field(
            name="id",
            type="id",
            show_index=False,
            show_create=False,
            show_detail=False,
        ),
        "name": Field(
            name="name",
        ),
    },
)
schema = Schema(models=[model])


def test_private_references() -> None:
    assert model._schema is schema
    assert model.fields["id"]._schema is schema
    assert model.fields["id"]._model is model


def test_label() -> None:
    assert model.label == "User"


def test_label_plural() -> None:
    assert model.label_plural == "Users"


def test_field_order() -> None:
    assert model.field_order == ["id", "name"]


def test_table_link_field() -> None:
    assert model.table_link_field == "name"


def test_show_in_search() -> None:
    assert model.show_in_search


def test_query_list() -> None:
    assert model.query_list == "users"


def test_query_item() -> None:
    assert model.query_single == "user"


def test_query_required_fields() -> None:
    assert model.query_required_fields == ["id", "name"]
