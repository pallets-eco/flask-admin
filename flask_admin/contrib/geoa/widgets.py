from wtforms.widgets import TextArea


def lat(pt):
    return getattr(pt, "lat", getattr(pt, "x", pt[0]))


def lng(pt):
    return getattr(pt, "lng", getattr(pt, "y", pt[1]))


class LeafletWidget(TextArea):
    data_role = 'leaflet'

    """
        `Leaflet <http://leafletjs.com/>`_ styled map widget. Inherits from
        `TextArea` so that geographic data can be stored via the <textarea>
        (and edited there if the user's browser does not have Javascript).

        You must include leaflet.js, form.js and leaflet stylesheet for it to
        work. You also need leaflet.draw.js (and its stylesheet) for it to be
        editable.
    """
    def __init__(
            self, width=300, height=300, center=None,
            zoom=None, min_zoom=None, max_zoom=None, max_bounds=None):
        self.width = width
        self.height = height
        self.center = center
        self.zoom = zoom
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.max_bounds = max_bounds

    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', self.data_role)
        gtype = getattr(field, "geometry_type", "GEOMETRY")
        kwargs.setdefault('data-geometry-type', gtype)

        # set optional values from constructor
        if not "data-width" in kwargs:
            kwargs["data-width"] = self.width
        if not "data-height" in kwargs:
            kwargs["data-height"] = self.height
        if self.center:
            kwargs["data-lat"] = lat(self.center)
            kwargs["data-lng"] = lng(self.center)
        if self.zoom:
            kwargs["data-zoom"] = self.zoom
        if self.min_zoom:
            kwargs["data-min-zoom"] = self.min_zoom
        if self.max_zoom:
            kwargs["data-max-zoom"] = self.max_zoom
        if self.max_bounds:
            if getattr(self.max_bounds, "bounds"):
                # this is a Shapely geometric object
                minx, miny, maxx, maxy = self.max_bounds.bounds
            elif len(self.max_bounds) == 4:
                # this is a list of four values
                minx, miny, maxx, maxy = self.max_bounds
            else:
                # this is a list of two points
                minx = lat(self.max_bounds[0])
                miny = lng(self.max_bounds[0])
                maxx = lat(self.max_bounds[1])
                maxy = lng(self.max_bounds[1])
            kwargs["data-max-bounds-sw-lat"] = minx
            kwargs["data-max-bounds-sw-lng"] = miny
            kwargs["data-max-bounds-ne-lat"] = maxx
            kwargs["data-max-bounds-ne-lng"] = maxy

        return super(LeafletWidget, self).__call__(field, **kwargs)
