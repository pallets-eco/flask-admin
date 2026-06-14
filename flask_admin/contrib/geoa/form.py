import typing as t

from flask_admin.contrib.sqla.form import AdminModelConverter as SQLAAdminConverter
from flask_admin.model.form import converts

from ..._types import T_COL_NO_STR
from .fields import GeoJSONField


class AdminModelConverter(SQLAAdminConverter):
    @converts("Geography", "Geometry")
    def convert_geom(
        self, column: T_COL_NO_STR, field_args: dict[str, t.Any], **extra: t.Any
    ) -> GeoJSONField:
        field_args["geometry_type"] = column.type.geometry_type  # type: ignore[union-attr]
        field_args["srid"] = column.type.srid  # type: ignore[union-attr]
        field_args["session"] = self.session
        field_args["tile_layer_url"] = self.view.tile_layer_url  # type: ignore[attr-defined]
        field_args["tile_layer_attribution"] = self.view.tile_layer_attribution  # type: ignore[attr-defined]
        return GeoJSONField(**field_args)
