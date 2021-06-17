from uuid import uuid4

import attr

from test_defaults import model


@attr.s(repr=False, eq=False, order=False, slots=True, kw_only=True, auto_attribs=True)
class User:
    id: int = attr.ib(factory=uuid4)
    name: str

    @property
    def display_value(self) -> str:
        return self.name


user = User(name="admin")


def test_get_display_value() -> None:
    assert model.get_display_value(user) == "admin"


def test_get_index_field_order() -> None:
    assert model.get_index_field_order() == ["name"]


def test_get_create_field_order() -> None:
    assert model.get_create_field_order() == ["name"]


def test_get_detail_field_order() -> None:
    assert model.get_detail_field_order() == ["name"]


def test_get_tooltip_field_order() -> None:
    assert model.get_tooltip_field_order() == []
