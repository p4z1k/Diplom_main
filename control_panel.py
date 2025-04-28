from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

class ControlPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        draw_panel = QHBoxLayout()
        self.start_btn = QPushButton("Начать рисование")
        self.save_btn = QPushButton("Сохранить участок")
        self.save_btn.setEnabled(False)
        draw_panel.addWidget(self.start_btn)
        draw_panel.addWidget(self.save_btn)
        
        harvest_panel = QHBoxLayout()
        self.add_harvest_btn = QPushButton("Добавить сбор")
        self.add_harvest_btn.setEnabled(False)
        
        self.history_btn = QPushButton("История сборов")
        self.history_btn.setEnabled(False)
        
        harvest_panel.addWidget(self.add_harvest_btn)
        harvest_panel.addWidget(self.history_btn)
        
        layout.addLayout(draw_panel)
        layout.addLayout(harvest_panel)