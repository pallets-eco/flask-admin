from collections.abc import Sequence
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING
from typing import Union

if TYPE_CHECKING:
    import sqlalchemy  # noqa

T_COLUMN_LIST = Sequence[Union[str, "sqlalchemy.Column"]]
T_FORMATTER = Callable[[Any, Any, Any], Any]
T_FORMATTERS = dict[type, T_FORMATTER]
