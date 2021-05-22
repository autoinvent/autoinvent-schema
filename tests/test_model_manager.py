from uuid import uuid4

import attr

from conveyor_schema.schema import Model
from conveyor_schema.schema import Schema

schema = Schema(
    models={
        "user": Model(
            name="user",
            label="User",
            label_plural="Users",
        ),
    },
)
user_model = schema.get_model("user")


@attr.dataclass(slots=True, kw_only=True)
class User:
    id: int = attr.ib(init=False, factory=uuid4)
    name: str

    @property
    def display_value(self) -> str:
        return self.name


user = User(name="admin")


def test_get_label() -> None:
    assert user_model.label(user, [user]) == "User"


def test_get_label_plural() -> None:
    assert user_model.label_plural(user, [user]) == "Users"


def test_get_display_value() -> None:
    assert user_model.display_value(user) == "admin"
