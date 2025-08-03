from traits.api import HasTraits, File
from traitsui.api import View, Item, FileEditor

class FilteredFileBrowserExample(HasTraits):
    """
    An example showing how to filter for specific file types.
    """
    file_path = File()

    view = View(
        Item('file_path',
             label="Select a YAML File",
             editor=FileEditor(filter=['*.yaml','*.yml']),
        ),
        title="YAML File Browser",
        buttons=['OK', 'Cancel'],
        resizable=True
    )

if __name__ == '__main__':
    filtered_browser_instance = FilteredFileBrowserExample()
    filtered_browser_instance.configure_traits()
    if filtered_browser_instance.file_path:
        print(f"\nYou selected the Python file: {filtered_browser_instance.file_path}")
    else:
        print("\nNo file was selected.")