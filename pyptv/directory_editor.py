#!/usr/bin/pythonw
"""
Implementation of a DirectoryEditor demo plugin for Traits UI demo program.
This demo shows each of the four styles of the DirectoryEditor
"""
# Imports:
from traits.api import HasTraits, Directory

from traitsui.api import Item, View

# Define the demo class:


class DirectoryEditorDialog(HasTraits):
    """Define the main DirectoryEditor demo class."""

    # Define a Directory trait to view:
    dir_name = Directory
    # Display specification (one Item per editor style):
    dir_item = Item("dir_name", style="simple", label="Simple")
    # Demo view:
    view = View(
        dir_item,
        title="Choose the experimental directory",
        buttons=["OK"],
        width=0.5,
        resizable=True,
        kind="modal",
    )


# Create the demo:
# demo = DirectoryEditorDemo()
# Run the demo (if invoked from the command line):
# if __name__ == '__main__':
# 	demo.configure_traits()
