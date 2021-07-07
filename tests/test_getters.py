import dataclasses
from uuid import uuid4

from test_defaults import model


@dataclasses.dataclass()
class User:
    name: str
    id: int = dataclasses.field(default_factory=uuid4)

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
