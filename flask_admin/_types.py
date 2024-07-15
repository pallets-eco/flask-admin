from typing import Union, Sequence, Dict, Callable

import sqlalchemy

T_COLUMN_LIST = Sequence[Union[str, sqlalchemy.Column]]
T_FORMATTERS = Dict[type, Callable]  # todo: Make this tighter
