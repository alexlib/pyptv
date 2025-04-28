#!/usr/bin/env python
"""
Draws a colormapped image plot
 - Left-drag pans the plot.
 - Mousewheel up and down zooms the plot in and out.
 - Pressing "z" brings up the Zoom Box, and you can click-drag a rectangular
   region to zoom.  If you use a sequence of zoom boxes, pressing alt-left-arrow
   and alt-right-arrow moves you forwards and backwards through the "zoom
   history".
"""

# Major library imports
from numpy import exp, linspace, meshgrid

# Enthought library imports
from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance
from traitsui.api import Item, Group, View

# Chaco imports
from chaco.api import ArrayPlotData, viridis, Plot, HPlotContainer, VPlotContainer
from chaco.tools.api import PanTool, ZoomTool
import imageio
from numpy import array

# ===============================================================================
# # Create the Chaco plot.
# ===============================================================================
def _create_plot_component():
    # Create a scalar field to colormap
    # Read the image from disk
    # Read images from disk
    images = []
    for cam in range(1, 5):
        image = imageio.imread(f'tests/test_cavity/img/cam{cam}.10000', mode='L')
        images.append(array(image))

    # Create a plot data object and give it this data
    pd = ArrayPlotData()
    for i, img in enumerate(images):
        pd.set_data(f"imagedata_{i}", img)

    # Create the plots
    plots = []
    for i in range(4):
        plot = Plot(pd)
        img_plot = plot.img_plot(
            f"imagedata_{i}", xbounds=(0, 10), ybounds=(0, 5), colormap=viridis
        )[0]

        # Tweak some of the plot properties
        plot.title = f"Camera {i+1}"
        plot.padding = 50

        # Attach some tools to the plot
        plot.tools.append(PanTool(plot))
        zoom = ZoomTool(component=img_plot, tool_mode="box", always_on=False)
        img_plot.overlays.append(zoom)

        plots.append(plot)

    # Create a container and add our plots in a 2x2 grid
    container = VPlotContainer(
        HPlotContainer(plots[0], plots[1]),
        HPlotContainer(plots[2], plots[3]),
        padding=40, fill_padding=True, bgcolor="white", use_backbuffer=True
    )
    return container


# ===============================================================================
# Attributes to use for the plot view.
size = (800, 600)
title = "Basic Colormapped Image Plot"

# ===============================================================================
# # Demo class that is used by the demo.py application.
# ===============================================================================
class Demo(HasTraits):
    plot = Instance(Component)

    traits_view = View(
        Group(
            Item("plot", editor=ComponentEditor(size=size), show_label=False),
            orientation="vertical",
        ),
        resizable=True,
        title=title,
    )

    def _plot_default(self):
        return _create_plot_component()


demo = Demo()

if __name__ == "__main__":
    demo.configure_traits()