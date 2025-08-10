"""Plugin management dialog for the PyPTV modern UI."""

import os
import sys
import importlib
from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QWidget,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QSplitter,
    QToolBar,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QComboBox,
    QTextEdit
)


class PluginListItem(QWidget):
    """Widget for displaying a plugin in a list."""
    
    def __init__(self, plugin_name, plugin_path, is_active=False, parent=None):
        """Initialize the plugin list item.
        
        Args:
            plugin_name: Name of the plugin
            plugin_path: Path to the plugin
            is_active: Whether the plugin is active
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path
        self.is_active = is_active
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_active)
        layout.addWidget(self.checkbox)
        
        # Create label
        self.label = QLabel(plugin_name)
        self.label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.label)
        
        # Add stretch
        layout.addStretch()
        
        # Create path label
        self.path_label = QLabel(str(plugin_path))
        self.path_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.path_label)


class PluginManagerDialog(QDialog):
    """Dialog for managing plugins in the modern UI."""
    
    def __init__(self, ptv_core=None, parent=None):
        """Initialize the plugin manager dialog.
        
        Args:
            ptv_core: PTVCore instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store PTV core
        self.ptv_core = ptv_core
        
        # Set dialog properties
        self.setWindowTitle("Plugin Manager")
        self.resize(800, 600)
        
        # Create layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Create sequence plugin tab
        self.sequence_tab = QWidget()
        self.sequence_layout = QVBoxLayout(self.sequence_tab)
        self.tabs.addTab(self.sequence_tab, "Sequence Plugins")
        
        # Create tracking plugin tab
        self.tracking_tab = QWidget()
        self.tracking_layout = QVBoxLayout(self.tracking_tab)
        self.tabs.addTab(self.tracking_tab, "Tracking Plugins")
        
        # Create import plugin tab
        self.import_tab = QWidget()
        self.import_layout = QVBoxLayout(self.import_tab)
        self.tabs.addTab(self.import_tab, "Import Plugin")
        
        # Initialize tabs
        self.initialize_sequence_tab()
        self.initialize_tracking_tab()
        self.initialize_import_tab()
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.close_button)
        
        self.main_layout.addLayout(button_layout)
        
        # Load plugins
        self.load_plugins()
    
    def initialize_sequence_tab(self):
        """Initialize the sequence plugin tab."""
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        self.add_sequence_action = QAction("Add Plugin", self)
        self.add_sequence_action.triggered.connect(self.add_sequence_plugin)
        toolbar.addAction(self.add_sequence_action)
        
        self.remove_sequence_action = QAction("Remove Plugin", self)
        self.remove_sequence_action.triggered.connect(self.remove_sequence_plugin)
        toolbar.addAction(self.remove_sequence_action)
        
        self.sequence_layout.addWidget(toolbar)
        
        # Create list widget
        self.sequence_list = QListWidget()
        self.sequence_layout.addWidget(self.sequence_list)
        
        # Create active plugin selection
        active_layout = QHBoxLayout()
        active_layout.addWidget(QLabel("Active Plugin:"))
        
        self.active_sequence_plugin = QComboBox()
        self.active_sequence_plugin.addItem("default")
        active_layout.addWidget(self.active_sequence_plugin)
        
        self.sequence_layout.addLayout(active_layout)
        
        # Create description
        self.sequence_description = QTextEdit()
        self.sequence_description.setReadOnly(True)
        self.sequence_description.setMaximumHeight(100)
        self.sequence_layout.addWidget(QLabel("Description:"))
        self.sequence_layout.addWidget(self.sequence_description)
    
    def initialize_tracking_tab(self):
        """Initialize the tracking plugin tab."""
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        self.add_tracking_action = QAction("Add Plugin", self)
        self.add_tracking_action.triggered.connect(self.add_tracking_plugin)
        toolbar.addAction(self.add_tracking_action)
        
        self.remove_tracking_action = QAction("Remove Plugin", self)
        self.remove_tracking_action.triggered.connect(self.remove_tracking_plugin)
        toolbar.addAction(self.remove_tracking_action)
        
        self.tracking_layout.addWidget(toolbar)
        
        # Create list widget
        self.tracking_list = QListWidget()
        self.tracking_layout.addWidget(self.tracking_list)
        
        # Create active plugin selection
        active_layout = QHBoxLayout()
        active_layout.addWidget(QLabel("Active Plugin:"))
        
        self.active_tracking_plugin = QComboBox()
        self.active_tracking_plugin.addItem("default")
        active_layout.addWidget(self.active_tracking_plugin)
        
        self.tracking_layout.addLayout(active_layout)
        
        # Create description
        self.tracking_description = QTextEdit()
        self.tracking_description.setReadOnly(True)
        self.tracking_description.setMaximumHeight(100)
        self.tracking_layout.addWidget(QLabel("Description:"))
        self.tracking_layout.addWidget(self.tracking_description)
    
    def initialize_import_tab(self):
        """Initialize the import plugin tab."""
        # Create plugin path field
        self.import_layout.addWidget(QLabel("Plugin Path:"))
        
        path_layout = QHBoxLayout()
        self.plugin_path = QLineEdit()
        path_layout.addWidget(self.plugin_path)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_plugin)
        path_layout.addWidget(browse_button)
        
        self.import_layout.addLayout(path_layout)
        
        # Create plugin name field
        self.import_layout.addWidget(QLabel("Plugin Name:"))
        self.plugin_name = QLineEdit()
        self.import_layout.addWidget(self.plugin_name)
        
        # Create plugin type field
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Plugin Type:"))
        
        self.plugin_type = QComboBox()
        self.plugin_type.addItems(["Sequence", "Tracking"])
        type_layout.addWidget(self.plugin_type)
        
        self.import_layout.addLayout(type_layout)
        
        # Create description field
        self.import_layout.addWidget(QLabel("Description:"))
        self.plugin_description = QTextEdit()
        self.import_layout.addWidget(self.plugin_description)
        
        # Create import button
        self.import_button = QPushButton("Import Plugin")
        self.import_button.clicked.connect(self.import_plugin)
        self.import_layout.addWidget(self.import_button)
        
        # Add stretch
        self.import_layout.addStretch()
    
    def load_plugins(self):
        """Load plugins from the PTV core."""
        if not self.ptv_core:
            return
            
        # Load sequence plugins
        self.sequence_list.clear()
        self.active_sequence_plugin.clear()
        self.active_sequence_plugin.addItem("default")
        
        if hasattr(self.ptv_core, 'plugins') and 'sequence' in self.ptv_core.plugins:
            for plugin in self.ptv_core.plugins['sequence']:
                if plugin != "default":
                    self.active_sequence_plugin.addItem(plugin)
                    item = QListWidgetItem(self.sequence_list)
                    item.setSizeHint(QSize(0, 40))
                    plugin_widget = PluginListItem(plugin, Path("plugins") / f"{plugin}.py", plugin == self.ptv_core.plugins.get('sequence_alg', 'default'))
                    self.sequence_list.setItemWidget(item, plugin_widget)
            
            # Set active plugin
            active_plugin = self.ptv_core.plugins.get('sequence_alg', 'default')
            index = self.active_sequence_plugin.findText(active_plugin)
            if index >= 0:
                self.active_sequence_plugin.setCurrentIndex(index)
        
        # Load tracking plugins
        self.tracking_list.clear()
        self.active_tracking_plugin.clear()
        self.active_tracking_plugin.addItem("default")
        
        if hasattr(self.ptv_core, 'plugins') and 'tracking' in self.ptv_core.plugins:
            for plugin in self.ptv_core.plugins['tracking']:
                if plugin != "default":
                    self.active_tracking_plugin.addItem(plugin)
                    item = QListWidgetItem(self.tracking_list)
                    item.setSizeHint(QSize(0, 40))
                    plugin_widget = PluginListItem(plugin, Path("plugins") / f"{plugin}.py", plugin == self.ptv_core.plugins.get('track_alg', 'default'))
                    self.tracking_list.setItemWidget(item, plugin_widget)
            
            # Set active plugin
            active_plugin = self.ptv_core.plugins.get('track_alg', 'default')
            index = self.active_tracking_plugin.findText(active_plugin)
            if index >= 0:
                self.active_tracking_plugin.setCurrentIndex(index)
    
    @Slot()
    def add_sequence_plugin(self):
        """Add a sequence plugin."""
        self.tabs.setCurrentIndex(2)  # Switch to import tab
        self.plugin_type.setCurrentIndex(0)  # Set type to sequence
        self.plugin_path.clear()
        self.plugin_name.clear()
        self.plugin_description.clear()
        QMessageBox.information(
            self, "Add Sequence Plugin", 
            "Please use the Import Plugin tab to add a new sequence plugin."
        )
    
    @Slot()
    def remove_sequence_plugin(self):
        """Remove a sequence plugin."""
        current_item = self.sequence_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Remove Plugin", 
                "Please select a plugin to remove."
            )
            return
            
        plugin_widget = self.sequence_list.itemWidget(current_item)
        
        # Ask for confirmation
        result = QMessageBox.question(
            self, 
            "Remove Plugin", 
            f"Are you sure you want to remove the plugin '{plugin_widget.plugin_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # Remove from list widget
            self.sequence_list.takeItem(self.sequence_list.row(current_item))
            
            # Remove from combobox
            index = self.active_sequence_plugin.findText(plugin_widget.plugin_name)
            if index >= 0:
                self.active_sequence_plugin.removeItem(index)
            
            # Update plugin list file (will be saved on apply)
    
    @Slot()
    def add_tracking_plugin(self):
        """Add a tracking plugin."""
        self.tabs.setCurrentIndex(2)  # Switch to import tab
        self.plugin_type.setCurrentIndex(1)  # Set type to tracking
        self.plugin_path.clear()
        self.plugin_name.clear()
        self.plugin_description.clear()
        QMessageBox.information(
            self, "Add Tracking Plugin", 
            "Please use the Import Plugin tab to add a new tracking plugin."
        )
    
    @Slot()
    def remove_tracking_plugin(self):
        """Remove a tracking plugin."""
        current_item = self.tracking_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Remove Plugin", 
                "Please select a plugin to remove."
            )
            return
            
        plugin_widget = self.tracking_list.itemWidget(current_item)
        
        # Ask for confirmation
        result = QMessageBox.question(
            self, 
            "Remove Plugin", 
            f"Are you sure you want to remove the plugin '{plugin_widget.plugin_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # Remove from list widget
            self.tracking_list.takeItem(self.tracking_list.row(current_item))
            
            # Remove from combobox
            index = self.active_tracking_plugin.findText(plugin_widget.plugin_name)
            if index >= 0:
                self.active_tracking_plugin.removeItem(index)
            
            # Update plugin list file (will be saved on apply)
    
    @Slot()
    def browse_plugin(self):
        """Browse for a plugin file."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Python files (*.py)")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                path = Path(file_paths[0])
                self.plugin_path.setText(str(path))
                
                # Set plugin name from filename
                self.plugin_name.setText(path.stem)
    
    @Slot()
    def import_plugin(self):
        """Import a plugin."""
        # Get plugin information
        plugin_path = self.plugin_path.text()
        plugin_name = self.plugin_name.text()
        plugin_type = self.plugin_type.currentText().lower()
        description = self.plugin_description.toPlainText()
        
        if not plugin_path or not plugin_name:
            QMessageBox.warning(
                self, "Import Plugin", 
                "Please provide a plugin path and name."
            )
            return
            
        # Check if path exists
        if not Path(plugin_path).exists():
            QMessageBox.warning(
                self, "Import Plugin", 
                f"The file '{plugin_path}' does not exist."
            )
            return
            
        # Try to import the plugin to verify it's valid
        try:
            # This is a placeholder for actual plugin validation
            # In a real implementation, you would check if the plugin has the required interface
            
            # Add to appropriate list and combobox
            if plugin_type == "sequence":
                item = QListWidgetItem(self.sequence_list)
                item.setSizeHint(QSize(0, 40))
                plugin_widget = PluginListItem(plugin_name, plugin_path, False)
                self.sequence_list.setItemWidget(item, plugin_widget)
                self.active_sequence_plugin.addItem(plugin_name)
            else:  # tracking
                item = QListWidgetItem(self.tracking_list)
                item.setSizeHint(QSize(0, 40))
                plugin_widget = PluginListItem(plugin_name, plugin_path, False)
                self.tracking_list.setItemWidget(item, plugin_widget)
                self.active_tracking_plugin.addItem(plugin_name)
            
            # Switch to appropriate tab
            self.tabs.setCurrentIndex(0 if plugin_type == "sequence" else 1)
            
            QMessageBox.information(
                self, "Import Plugin", 
                f"Successfully imported plugin '{plugin_name}'."
            )
            
            # Clear fields
            self.plugin_path.clear()
            self.plugin_name.clear()
            self.plugin_description.clear()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Import Plugin", 
                f"Error importing plugin: {e}"
            )
    
    @Slot()
    def apply(self):
        """Apply changes to plugins."""
        if not self.ptv_core:
            self.accept()
            return
            
        try:
            # Update active plugins
            active_sequence = self.active_sequence_plugin.currentText()
            active_tracking = self.active_tracking_plugin.currentText()
            
            if hasattr(self.ptv_core, 'plugins'):
                if hasattr(self.ptv_core.plugins, 'track_alg'):
                    self.ptv_core.plugins.track_alg = active_tracking
                else:
                    self.ptv_core.plugins['track_alg'] = active_tracking
                    
                if hasattr(self.ptv_core.plugins, 'sequence_alg'):
                    self.ptv_core.plugins.sequence_alg = active_sequence
                else:
                    self.ptv_core.plugins['sequence_alg'] = active_sequence
            
            # Save sequence plugins
            sequence_plugins = []
            for i in range(self.sequence_list.count()):
                item = self.sequence_list.item(i)
                plugin_widget = self.sequence_list.itemWidget(item)
                sequence_plugins.append(plugin_widget.plugin_name)
            
            # Save tracking plugins
            tracking_plugins = []
            for i in range(self.tracking_list.count()):
                item = self.tracking_list.item(i)
                plugin_widget = self.tracking_list.itemWidget(item)
                tracking_plugins.append(plugin_widget.plugin_name)
            
            # Save plugins to files
            self.save_plugins_to_files(sequence_plugins, tracking_plugins)
            
            QMessageBox.information(
                self, "Plugin Manager", 
                "Plugin settings applied successfully."
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Plugin Manager", 
                f"Error applying plugin settings: {e}"
            )
    
    def save_plugins_to_files(self, sequence_plugins, tracking_plugins):
        """Save plugins to files.
        
        Args:
            sequence_plugins: List of sequence plugin names
            tracking_plugins: List of tracking plugin names
        """
        # Get working directory (where the plugin files should be saved)
        working_dir = Path.cwd()
        
        # Save sequence plugins
        sequence_file = working_dir / "sequence_plugins.txt"
        with open(sequence_file, "w", encoding="utf8") as f:
            f.write("\n".join(sequence_plugins))
        
        # Save tracking plugins
        tracking_file = working_dir / "tracking_plugins.txt"
        with open(tracking_file, "w", encoding="utf8") as f:
            f.write("\n".join(tracking_plugins))
        
        # Update PTV core plugins if available
        if self.ptv_core and hasattr(self.ptv_core, 'plugins'):
            if 'sequence' in self.ptv_core.plugins:
                self.ptv_core.plugins['sequence'] = ['default'] + sequence_plugins
            if 'tracking' in self.ptv_core.plugins:
                self.ptv_core.plugins['tracking'] = ['default'] + tracking_plugins