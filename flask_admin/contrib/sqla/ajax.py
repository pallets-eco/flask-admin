from sqlalchemy import and_
from sqlalchemy import cast
from sqlalchemy import or_
from sqlalchemy import text
from sqlalchemy.types import String

from flask_admin._compat import as_unicode
from flask_admin._compat import string_types
from flask_admin.model.ajax import AjaxModelLoader
from flask_admin.model.ajax import DEFAULT_PAGE_SIZE

from .tools import get_primary_key
from .tools import has_multiple_pks
from .tools import is_association_proxy
from .tools import is_relationship


class QueryAjaxModelLoader(AjaxModelLoader):
    def __init__(self, name, session, model, **options):
        """
        Constructor.

        :param fields:
            Fields to run query against
        :param filters:
            Additional filters to apply to the loader
        """
        super().__init__(name, options)

        self.session = session
        self.model = model
        self.fields = options.get("fields")
        self.order_by = options.get("order_by")
        self.filters = options.get("filters")

        if not self.fields:
            raise ValueError(
                f"AJAX loading requires `fields` to be specified for"
                f" {model}.{self.name}"
            )

        self._cached_fields = self._process_fields()

        if has_multiple_pks(model):
            raise NotImplementedError(
                "Flask-Admin does not support multi-pk AJAX model loading."
            )

        self.pk = get_primary_key(model)

    def _process_fields(self):
        remote_fields = []

        for field in self.fields:
            if isinstance(field, string_types):
                attr = getattr(self.model, field, None)

                if not attr:
                    raise ValueError(f"{self.model}.{field} does not exist.")

                remote_fields.append(attr)
            else:
                # TODO: Figure out if it is valid SQLAlchemy property?
                remote_fields.append(field)

        return remote_fields

    def format(self, model):
        if not model:
            return None

        return getattr(model, self.pk), as_unicode(model)

    def get_query(self):
        return self.session.query(self.model)

    def get_one(self, pk):
        # prevent autoflush from occuring during populate_obj
        with self.session.no_autoflush:
            return self.session.get(self.model, pk)

    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.get_query()

        # no type casting to string if a ColumnAssociationProxyInstance is given
        filters = (
            field.ilike(f"%{term}%")
            if is_association_proxy(field)
            else cast(field, String).ilike(f"%{term}%")
            for field in self._cached_fields
        )
        query = query.filter(or_(*filters))

        if self.filters:
            filters = [
                text(f"{self.model.__tablename__.lower()}.{value}")
                for value in self.filters
            ]
            query = query.filter(and_(*filters))

        if self.order_by:
            query = query.order_by(self.order_by)

        return query.offset(offset).limit(limit).all()


def create_ajax_loader(model, session, name, field_name, options):
    attr = getattr(model, field_name, None)

    if attr is None:
        raise ValueError(f"Model {model} does not have field {field_name}.")

    if not is_relationship(attr) and not is_association_proxy(attr):
        raise ValueError(f"{model}.{field_name} is not a relation.")

    if is_association_proxy(attr):
        attr = attr.remote_attr

    remote_model = attr.prop.mapper.class_
    return QueryAjaxModelLoader(name, session, remote_model, **options)
