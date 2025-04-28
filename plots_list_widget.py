from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QLineEdit, QComboBox, QLabel
)
from PyQt5.QtCore import Qt

class PlotsListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        filter_panel = QWidget()
        filter_layout = QHBoxLayout(filter_panel)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию...")
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['Все', 'Собственный', 'Арендованный'])
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['По названию', 'По площади', 'По типу'])
        
        filter_layout.addWidget(self.search_edit)
        filter_layout.addWidget(QLabel("Фильтр:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(QLabel("Сортировка:"))
        filter_layout.addWidget(self.sort_combo)
        
        self.plot_list = QListWidget()
        self.plot_list.setContextMenuPolicy(Qt.CustomContextMenu)
        
        layout.addWidget(filter_panel)
        layout.addWidget(self.plot_list)