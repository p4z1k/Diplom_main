from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, 
    QLineEdit, QDialogButtonBox, QDateEdit,QDateEdit,
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QDoubleValidator

class HarvestDialog(QDialog):
    def __init__(self, parent=None, existing_cultures=None, record=None):
        super().__init__(parent)
        self.existing_cultures = existing_cultures or []
        self.record = record
        self.setWindowTitle("Редактирование сбора урожая" if record else "Добавление сбора урожая")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.culture_combo = QComboBox()
        self.culture_combo.setEditable(True)
        self.culture_combo.addItems(sorted(set(self.existing_cultures)))
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("Количество в тоннах")
        self.amount_edit.setValidator(QDoubleValidator(0, 9999, 2))
        
        if self.record:
            self.date_edit.setDate(QDate.fromString(self.record['date'], "yyyy-MM-dd"))
            self.culture_combo.setCurrentText(self.record['culture'])
            self.amount_edit.setText(f"{self.record['amount']:.2f}")
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(QLabel("Дата сбора:"))
        layout.addWidget(self.date_edit)
        layout.addWidget(QLabel("Культура:"))
        layout.addWidget(self.culture_combo)
        layout.addWidget(QLabel("Количество (тонн):"))
        layout.addWidget(self.amount_edit)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self):
        return {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "culture": self.culture_combo.currentText(),
            "amount": float(self.amount_edit.text()) if self.amount_edit.text() else 0.0
        }