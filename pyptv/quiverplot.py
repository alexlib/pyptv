# Chaco relative imports
from chaco.api import AbstractDataSource
from chaco.api import ScatterPlot

# Enthought library imports
from enable.api import ColorTrait
from numpy import (
    array,
    compress,
    matrix,
    newaxis,
    sqrt,
    transpose,
    invert,
    isnan,
)
from traits.api import Array, Enum, Float, Instance, Int


class QuiverPlot(ScatterPlot):

    # Determines how to interpret the data in the **vectors** data source.
    # 	"vector": each tuple is a (dx, dy)
    # 	"radial": each tuple is an (r, theta)
    data_type = Enum("vector", "radial")  # TODO: implement "radial"

    # A datasource that returns an Nx2 array array indicating directions
    # of the vectors.  The interpretation of this array is dependent on
    # the setting of the **data_type** attribute.
    #
    # Usually this will be a MultiArrayDataSource.
    vectors = Instance(AbstractDataSource)

    # ------------------------------------------------------------------------
    # Visual attributes of the vector
    # ------------------------------------------------------------------------

    # The color of the lines
    line_color = ColorTrait("black")

    # The width of the lines
    line_width = Float(1.0)

    # The length, in pixels, of the arrowhead
    arrow_size = Int(5)

    # ------------------------------------------------------------------------
    # Private traits
    # ------------------------------------------------------------------------

    _cached_vector_data = Array
    _selected_vector_data = Array

    def _gather_points_old(self):
        """
        Collects the data points that are within the bounds of the plot and
        caches them
        Overrides scatterplot's function
        """
        if self._cache_valid and self._selection_cache_valid:
            return

        if not self.index or not self.value:
            return

        index, index_mask = self.index.get_data_mask()
        value, value_mask = self.value.get_data_mask()
        ep_index, ep_value = self.ep_index, self.ep_value
        if len(index) == 0 or len(value) == 0 or len(index) != len(value):
            self._cached_data_pts = []
            self._cached_point_mask = []
            self._cache_valid = True
            return

        index_range_mask = self.index_mapper.range.mask_data(index)
        value_range_mask = self.value_mapper.range.mask_data(value)
        ep_index_mask = self.index_mapper.range.mask_data(ep_index)
        ep_value_mask = self.value_mapper.range.mask_data(ep_value)

        nan_mask = (
            invert(isnan(index))
            & index_mask
            & invert(isnan(value))
            & value_mask
        )
        point_mask = (
            nan_mask
            & index_range_mask
            & value_range_mask
            & ep_index_mask
            & ep_value_mask
        )
        if not self._cache_valid:
            points = transpose(array((index, value)))
            endpoints = transpose(array((ep_index, ep_value)))
            self._cached_data_pts = compress(point_mask, points, axis=0)
            self._cached_end_epts = compress(point_mask, endpoints, axis=0)
            self._cached_point_mask = point_mask[:]
            self._cache_valid = True

        return

    def _render(self, gc, points, icon_mode=False):
        gc.save_state()
        gc.clip_to_rect(self.x, self.y, self.width, self.height)
        # print "inside render"
        gc.set_stroke_color(self.line_color_)
        gc.set_line_width(self.line_width)

        # Draw the body of the arrow
        starts = points
        ends = self.map_screen(self._cached_end_epts)

        if len(starts) > 0:
            gc.begin_path()
            gc.line_set(starts, ends)
            # gc.line_set(starts, self.end_points)
            gc.stroke_path()

        if self.arrow_size > 0:
            vec = self._cached_vector_data
            unit_vec = vec / sqrt(vec[:, 0] ** 2 + vec[:, 1] ** 2)[:, newaxis]
            a = 0.707106781  # sqrt(2)/2

            # Draw the left arrowhead (for an arrow pointing straight up)
            arrow_ends = (
                ends
                - array(unit_vec * matrix([[a, a], [-a, a]])) * self.arrow_size
            )
            gc.begin_path()
            gc.line_set(ends, arrow_ends)
            gc.stroke_path()

            # Draw the left arrowhead (for an arrow pointing straight up)
            arrow_ends = (
                ends
                - array(unit_vec * matrix([[a, -a], [a, a]])) * self.arrow_size
            )
            gc.begin_path()
            gc.line_set(ends, arrow_ends)
            gc.stroke_path()

        gc.restore_state()
