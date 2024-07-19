from typing import Union, Sequence, Dict, Callable, Any

import sqlalchemy

T_COLUMN_LIST = Sequence[Union[str, sqlalchemy.Column]]
T_FORMATTER = Callable[[Any, Any, Any], Any]
T_FORMATTERS = Dict[type, T_FORMATTER]
