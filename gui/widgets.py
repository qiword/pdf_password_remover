from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt

class CheckableListWidget(QListWidget):
    """带复选框的列表控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.itemChanged.connect(self.on_item_changed)
        
    def add_checkable_item(self, text, file_path, checked=True):
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, file_path)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self.addItem(item)
        
    def get_checked_files(self):
        checked_files = []
        for i in range(self.count()):
            item = self.item(i)
            if item.checkState() == Qt.Checked:
                checked_files.append(item.data(Qt.UserRole))
        return checked_files
    
    def select_all(self, checked=True):
        for i in range(self.count()):
            item = self.item(i)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
    
    def invert_selection(self):
        for i in range(self.count()):
            item = self.item(i)
            item.setCheckState(
                Qt.Unchecked if item.checkState() == Qt.Checked 
                else Qt.Checked
            )
    
    def on_item_changed(self, item):
        pass