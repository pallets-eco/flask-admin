import typing as t

DEFAULT_PAGE_SIZE = 10


class AjaxModelLoader:
    """
    Ajax related model loader. Override this to implement custom loading behavior.
    """

    def __init__(self, name: str, options: dict) -> None:
        """
        Constructor.

        :param name:
            Field name
        """
        self.name = name
        self.options = options

    def format(self, model: t.Union[None, str, bytes]) -> t.Optional[tuple[t.Any, str]]:
        """
        Return (id, name) tuple from the model.
        """
        raise NotImplementedError()

    def get_one(self, pk: t.Any) -> t.Any:
        """
        Find model by its primary key.

        :param pk:
            Primary key value
        """
        raise NotImplementedError()

    def get_list(
        self, query: str, offset: int = 0, limit: int = DEFAULT_PAGE_SIZE
    ) -> list:
        """
        Return models that match `query`.

        :param view:
            Administrative view.
        :param query:
            Query string
        :param offset:
            Offset
        :param limit:
            Limit
        """
        raise NotImplementedError()
