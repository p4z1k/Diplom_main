from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QDialogButtonBox,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor

class StatusSettingsDialog(QDialog):
    def __init__(self, parent=None, status_settings=None):
        super().__init__(parent)
        self.status_settings = status_settings or {
            "default_flow": [],
            "status_times": {}
        }
        self.setWindowTitle("Настройки статусов")
        self.setup_ui()
        self.update_time_table()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(1)
        self.status_table.setHorizontalHeaderLabels(["Последовательность статусов"])
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.status_table.setDragDropMode(QAbstractItemView.InternalMove)
        self.status_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.status_table.setDragEnabled(True)
        self.status_table.setAcceptDrops(True)
        self.status_table.setDropIndicatorShown(True)
        self.status_table.model().rowsMoved.connect(self.update_time_table)

        self.time_table = QTableWidget()
        self.time_table.setColumnCount(2)
        self.time_table.setHorizontalHeaderLabels(["Статус", "Дней до следующего"])
        self.time_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить статус")
        self.add_btn.clicked.connect(self.add_status)
        
        self.remove_btn = QPushButton("Удалить статус")
        self.remove_btn.clicked.connect(self.remove_status)
        
        self.move_up_btn = QPushButton("Вверх")
        self.move_up_btn.clicked.connect(self.move_up)
        
        self.move_down_btn = QPushButton("Вниз")
        self.move_down_btn.clicked.connect(self.move_down)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.move_up_btn)
        btn_layout.addWidget(self.move_down_btn)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(QLabel("Порядок статусов:"))
        layout.addWidget(self.status_table)
        layout.addWidget(QLabel("Время для статусов:"))
        layout.addWidget(self.time_table)
        layout.addLayout(btn_layout)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        self.status_table.setRowCount(len(self.status_settings["default_flow"]))
        for i, status in enumerate(self.status_settings["default_flow"]):
            item = QTableWidgetItem(status)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.status_table.setItem(i, 0, item)
        
        self.update_time_table()

    def update_time_table(self):

        current_values = {}
        for i in range(self.time_table.rowCount()):
            status = self.time_table.item(i, 0).text()
            days = self.time_table.item(i, 1).text()
            if status and days:
                current_values[status] = days
        
        self.time_table.setRowCount(self.status_table.rowCount())
        
        for i in range(self.status_table.rowCount()):
            status = self.status_table.item(i, 0).text()
            

            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.time_table.setItem(i, 0, status_item)
            
            days_item = QTableWidgetItem()
            days_item.setFlags(days_item.flags() | Qt.ItemIsEditable)
            

            if status in current_values:
                days_item.setText(current_values[status])
            elif status in self.status_settings["status_times"]:
                days_item.setText(str(self.status_settings["status_times"][status]))
            else:
                days_item.setText("0")
                
            self.time_table.setItem(i, 1, days_item)

    def add_status(self):
        row = self.status_table.rowCount()
        self.status_table.insertRow(row)
        item = QTableWidgetItem("Новый статус")
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.status_table.setItem(row, 0, item)
        self.update_time_table()

    def remove_status(self):
        current_row = self.status_table.currentRow()
        if current_row >= 0:
            self.status_table.removeRow(current_row)
            self.update_time_table()

    def move_up(self):
        current_row = self.status_table.currentRow()
        if current_row > 0:
            self.swap_rows(current_row, current_row - 1)
            self.status_table.setCurrentCell(current_row - 1, 0)

    def move_down(self):
        current_row = self.status_table.currentRow()
        if current_row < self.status_table.rowCount() - 1:
            self.swap_rows(current_row, current_row + 1)
            self.status_table.setCurrentCell(current_row + 1, 0)

    def swap_rows(self, row1, row2):
        item1 = self.status_table.takeItem(row1, 0)
        item2 = self.status_table.takeItem(row2, 0)
        self.status_table.setItem(row2, 0, item1)
        self.status_table.setItem(row1, 0, item2)
        self.update_time_table()

    def get_settings(self):
        self.status_settings["default_flow"] = [
            self.status_table.item(i, 0).text() 
            for i in range(self.status_table.rowCount())
        ]
        
        self.status_settings["status_times"] = {
            self.time_table.item(i, 0).text(): int(self.time_table.item(i, 1).text() or 0)
            for i in range(self.time_table.rowCount())
        }
        return self.status_settings