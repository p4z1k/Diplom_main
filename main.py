import sys
import os
from datetime import datetime
os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--remote-debugging-port=9222'

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QMessageBox, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDateEdit, QMenu, QTabWidget, QCheckBox,
    QStatusBar, QDialog, QGroupBox, QFormLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QDoubleValidator

from map_widget import MapWidget
from land_plots_manager import LandPlotManager
from plot_wizard import PlotWizard
from harvest_dialog import HarvestDialog
from status_dialog import StatusSettingsDialog
from status_manager import StatusManager
from harvest_manager import HarvestManager
from map_loader import cleanup_temp_files

class StatusChecker(QThread):
    status_updated = pyqtSignal()

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.active = True
        self.plot_manager = None

    def run(self):
        self.plot_manager = LandPlotManager(self.db_path)
        while self.active:
            self.check_statuses()
            self.sleep(60)

    def check_statuses(self):
        updated = False
        plots = self.plot_manager.get_all_plots()
        for plot in plots:
            if plot.get('auto_status', True):
                status = plot.get('status')
                changed = plot.get('status_changed')
                if status and changed:
                    wait_days = self.plot_manager.get_status_wait_time(status)
                    if wait_days > 0:
                        changed_date = QDate.fromString(changed[:10], "yyyy-MM-dd")
                        days_passed = changed_date.daysTo(QDate.currentDate())
                        if days_passed >= wait_days:
                            next_status = self.plot_manager.get_next_status(status)
                            if next_status:
                                self.plot_manager.update_plot_status(plot['id'], next_status)
                                updated = True
        if updated:
            self.status_updated.emit()

    def stop(self):
        self.active = False
        if not self.wait(500):
            self.terminate()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = "full_data.db"
        self.plot_manager = LandPlotManager(self.db_path)
        self.current_plot_id = None
        self.status_manager = StatusManager(self.plot_manager)
        self.harvest_manager = HarvestManager(self.plot_manager)
        self.init_ui()
        self.status_checker = StatusChecker(self.db_path)
        self.status_checker.status_updated.connect(self.update_tasks_table)
        self.status_checker.start()
        self.status_manager.status_updated.connect(self.update_tasks_table)

    def make_auto_status_handler(self, plot):
        def handler(state):
            self.toggle_auto_status(plot, state)
        return handler

    def make_task_action_handler(self, plot):
        def handler():
            self.status_manager.complete_task(plot)
            self.update_tasks_table()
        return handler

    def make_task_restart_handler(self, plot):
        def handler():
            self.status_manager.restart_status_cycle(plot)
            self.update_tasks_table()
        return handler

    def init_ui(self):
        self.setWindowTitle("Управление сельскохозяйственными участками")
        self.setGeometry(100, 100, 1400, 900)
      
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        self.plots_tab = QWidget()
        self.init_plots_tab()
        self.tab_widget.addTab(self.plots_tab, "Участки")

        self.tasks_tab = QWidget()
        self.init_tasks_tab()
        self.tab_widget.addTab(self.tasks_tab, "Текущие дела")
        
        self.statusBar().showMessage("Готово")

    def init_plots_tab(self):
        main_layout = QHBoxLayout(self.plots_tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        control_panel = QHBoxLayout()
        self.add_plot_btn = QPushButton("Добавить участок")
        self.add_plot_btn.clicked.connect(self.show_plot_wizard)
        control_panel.addWidget(self.add_plot_btn)

        filter_panel = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск участков...")
        self.search_edit.textChanged.connect(self.update_plot_list)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['Все', 'Собственный', 'Арендованный'])
        self.filter_combo.currentTextChanged.connect(self.update_plot_list)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['По названию', 'По площади', 'По типу'])
        self.sort_combo.currentTextChanged.connect(self.update_plot_list)
        
        filter_panel.addWidget(self.search_edit)
        filter_panel.addWidget(QLabel("Фильтр:"))
        filter_panel.addWidget(self.filter_combo)
        filter_panel.addWidget(QLabel("Сортировка:"))
        filter_panel.addWidget(self.sort_combo)

        self.plots_list = QListWidget()
        self.plots_list.itemClicked.connect(self.on_plot_selected)
        self.plots_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.plots_list.customContextMenuRequested.connect(self.show_plot_context_menu)
        
        left_panel.addLayout(control_panel)
        left_panel.addLayout(filter_panel)
        left_panel.addWidget(self.plots_list)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        self.map_widget = MapWidget()
        self.map_widget.setMinimumSize(800, 500)
        right_panel.addWidget(self.map_widget, stretch=2)

        harvest_group = QGroupBox("История сборов урожая")
        harvest_layout = QVBoxLayout()
        
        harvest_filter_panel = QHBoxLayout()
        harvest_filter_panel.addWidget(QLabel("Период:"))
        
        self.harvest_date_from = QDateEdit(QDate.currentDate().addMonths(-1))
        self.harvest_date_from.setDisplayFormat("dd.MM.yyyy")
        self.harvest_date_from.dateChanged.connect(self.update_harvest_history)
        harvest_filter_panel.addWidget(self.harvest_date_from)
        
        harvest_filter_panel.addWidget(QLabel("-"))
        
        self.harvest_date_to = QDateEdit(QDate.currentDate())
        self.harvest_date_to.setDisplayFormat("dd.MM.yyyy")
        self.harvest_date_to.dateChanged.connect(self.update_harvest_history)
        harvest_filter_panel.addWidget(self.harvest_date_to)
        
        harvest_filter_panel.addWidget(QLabel("Культура:"))
        
        self.harvest_culture_filter = QComboBox()
        self.harvest_culture_filter.addItem("Все культуры")
        self.harvest_culture_filter.currentTextChanged.connect(self.update_harvest_history)
        harvest_filter_panel.addWidget(self.harvest_culture_filter)
        
        self.harvest_table = QTableWidget()
        self.harvest_table.setColumnCount(4)
        self.harvest_table.setHorizontalHeaderLabels(["Дата", "Культура", "Количество (т)", "Действия"])
        self.harvest_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.harvest_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.harvest_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.add_harvest_btn = QPushButton("Добавить сбор урожая")
        self.add_harvest_btn.clicked.connect(self.add_harvest)
        self.add_harvest_btn.setEnabled(False)
        
        harvest_layout.addLayout(harvest_filter_panel)
        harvest_layout.addWidget(self.harvest_table)
        harvest_layout.addWidget(self.add_harvest_btn)
        harvest_group.setLayout(harvest_layout)
        
        right_panel.addWidget(harvest_group, stretch=1)

        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addLayout(right_panel, stretch=5)

        self.update_plot_list()

    def init_tasks_tab(self):
        layout = QVBoxLayout(self.tasks_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "Участок", "Статус", "Дней осталось", "Авто", "Действие", "Состояние"
        ])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tasks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        buttons_panel = QHBoxLayout()
        
        self.settings_btn = QPushButton("Настройки статусов")
        self.settings_btn.clicked.connect(self.show_status_settings)
        
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.update_tasks_table)
        
        buttons_panel.addWidget(self.settings_btn)
        buttons_panel.addWidget(self.refresh_btn)
        buttons_panel.addStretch()
        
        layout.addWidget(self.tasks_table)
        layout.addLayout(buttons_panel)
        
        self.update_tasks_table()

    def show_plot_wizard(self):
        wizard = PlotWizard(self)
        if wizard.exec_() == QDialog.Accepted:
            plot_data = wizard.get_data()
            self.save_new_plot(plot_data)

    def save_new_plot(self, plot_data):
        try:
            first_status = self.plot_manager.status_settings["default_flow"][0] if self.plot_manager.status_settings["default_flow"] else "Новый"

            self.plot_manager.add_plot(
                name=plot_data["name"],
                coordinates=plot_data["coordinates"],
                area=plot_data["area_ha"],
                plot_type=plot_data["plot_type"],
                status=first_status,
                additional_data={
                    "cadastral_number": plot_data["cadastral_number"],
                    "property_type": plot_data["property_type"],
                    "assignment_date": plot_data["assignment_date"],
                    "address": plot_data["address"],
                    "area_sqm": plot_data["area_sqm"],
                    "land_category": plot_data["land_category"],
                    "land_use": plot_data["land_use"],
                    "cadastral_value": plot_data["cadastral_value"],
                    "owner_name": plot_data["owner_name"],
                    "owner_contacts": plot_data["owner_contacts"]
                }
            )
            self.update_plot_list()
            QMessageBox.information(self, "Успех", "Участок успешно добавлен")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить участок: {str(e)}")

    def update_plot_list(self):
        sort_mapping = {
            'По названию': 'name',
            'По площади': 'area',
            'По типу': 'type'
        }
        
        filter_type = self.filter_combo.currentText()
        if filter_type == 'Все':
            filter_type = None
        
        self.plots_list.clear()
        
        plots = self.plot_manager.get_all_plots(
            sort_key=sort_mapping[self.sort_combo.currentText()],
            filter_type=filter_type,
            search_query=self.search_edit.text()
        )
        
        for plot in plots:
            plot_type = plot.get('type', 'Собственный')
            status = plot.get('status', 'Не задан')
            self.plots_list.addItem(
                f"{plot['id']}. {plot['name']} - "
                f"{plot.get('area_ha', plot.get('area', 0)):.2f} га ({status})"
            )

    def update_harvest_history(self):
        if not self.current_plot_id:
            return
            
        date_from = self.harvest_date_from.date().toString("yyyy-MM-dd")
        date_to = self.harvest_date_to.date().toString("yyyy-MM-dd")
        culture_filter = self.harvest_culture_filter.currentText()
        
        self.harvest_table.setProperty('date_from', date_from)
        self.harvest_table.setProperty('date_to', date_to)
        self.harvest_table.setProperty('culture_filter', culture_filter)
        
        self.harvest_manager.update_harvest_history(
            self.harvest_table,
            self.current_plot_id,
            date_from,
            date_to,
            culture_filter if culture_filter != "Все культуры" else None
        )

    def update_tasks_table(self):
        self.tasks_table.setRowCount(0)
        plots = self.plot_manager.get_all_plots()

        for plot in plots:
            status = plot.get('status', 'Не задан')
            days_left = self.status_manager.calculate_days_left(plot)

            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)

            self.tasks_table.setItem(row, 0, QTableWidgetItem(plot['name']))
            self.tasks_table.setItem(row, 1, QTableWidgetItem(status))

            days_item = QTableWidgetItem(str(days_left) if days_left != "∞" else "∞")
            self.tasks_table.setItem(row, 2, days_item)

            auto_check = QCheckBox()
            auto_check.setChecked(plot.get('auto_status', True))
            auto_check.stateChanged.connect(self.make_auto_status_handler(plot))
            self.tasks_table.setCellWidget(row, 3, auto_check)

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)

            next_status = self.plot_manager.get_next_status(status)
            if next_status:
                btn = QPushButton(f"Перейти к '{next_status}'")
                btn.clicked.connect(self.make_task_action_handler(plot))
                action_layout.addWidget(btn)
            elif status in self.plot_manager.status_settings["default_flow"]:
                btn = QPushButton(f"Начать цикл заново")
                btn.setStyleSheet("background-color: #4CAF50; color: white;")
                btn.clicked.connect(self.make_task_restart_handler(plot))
                action_layout.addWidget(btn)

            self.tasks_table.setCellWidget(row, 4, action_widget)

            state = self.status_manager.get_task_state(plot, days_left)
            state_widget = QLabel(state)

            if "Просрочено" in state:
                state_widget.setStyleSheet("color: red;")
            elif "Срочно" in state:
                state_widget.setStyleSheet("color: orange;")
            elif "Активно" in state:
                state_widget.setStyleSheet("color: green;")
            else:
                state_widget.setStyleSheet("color: blue;")

            self.tasks_table.setCellWidget(row, 5, state_widget)

    def refresh_all(self):
        self.update_plot_list()
        self.update_tasks_table()
        if self.current_plot_id:
            self.update_harvest_history()

    def handle_task_action(self, plot):
        self.status_manager.complete_task(plot)
        self.refresh_all()


    def handle_task_restart(self, plot):
        self.status_manager.restart_status_cycle(plot)
        self.refresh_all()


    def on_plot_selected(self, item):
        try:
            self.current_plot_id = int(item.text().split(".")[0])
            plot = self.plot_manager.get_plot_by_id(self.current_plot_id)
            if plot:
                self.map_widget.draw_existing_plot(plot['coordinates'])
                self.add_harvest_btn.setEnabled(True)
                
                harvests = self.plot_manager.get_harvests_for_plot(self.current_plot_id)
                cultures = sorted({h['culture'] for h in harvests if h['culture']})
                self.harvest_culture_filter.clear()
                self.harvest_culture_filter.addItem("Все культуры")
                for culture in cultures:
                    self.harvest_culture_filter.addItem(culture)
                
                self.refresh_all()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить участок: {str(e)}")
            self.current_plot_id = None
            self.add_harvest_btn.setEnabled(False)

    def add_harvest(self):
        if not self.current_plot_id:
            return
            
        plot = self.plot_manager.get_plot_by_id(self.current_plot_id)
        existing_cultures = list(set(
            record['culture'] for record in self.plot_manager.get_harvests_for_plot(self.current_plot_id)
        ))
        
        dialog = HarvestDialog(self, existing_cultures)
        if dialog.exec_() == QDialog.Accepted:
            harvest_data = dialog.get_data()
            self.plot_manager.add_harvest_record(
                self.current_plot_id,
                harvest_data['date'],
                harvest_data['culture'],
                harvest_data['amount']
            )
            self.refresh_all()


    def show_status_settings(self):
        dialog = StatusSettingsDialog(self, self.plot_manager.status_settings)
        if dialog.exec_() == QDialog.Accepted:
            self.plot_manager.status_settings = dialog.get_settings()
            self.plot_manager.save_status_settings()
            self.refresh_all()
            self.statusBar().showMessage("Настройки статусов сохранены", 3000)

    def toggle_auto_status(self, plot, state):
        self.plot_manager.update_plot(plot['id'], auto_status=state == Qt.Checked)
        self.statusBar().showMessage(
            f"Автоизменение статуса для {plot['name']} {'включено' if state else 'отключено'}", 
            3000
        )

    def show_plot_context_menu(self, pos):
        item = self.plots_list.itemAt(pos)
        if item:
            menu = QMenu()
            edit_action = menu.addAction("Редактировать")
            delete_action = menu.addAction("Удалить")
            
            action = menu.exec_(self.plots_list.mapToGlobal(pos))
            
            if action == edit_action:
                self.edit_plot(item)
            elif action == delete_action:
                self.delete_plot(item)

    def edit_plot(self, item):
        plot_id = int(item.text().split(".")[0])
        plot = self.plot_manager.get_plot_by_id(plot_id)
        if plot:
            dialog = PlotWizard(self)
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                self.plot_manager.update_plot(
                    plot_id,
                    name=new_data['cadastral_number'],
                    area=new_data['area_ha'],
                    type="Собственный",
                    additional_data={
                        "cadastral_number": new_data["cadastral_number"],
                        "property_type": new_data["property_type"],
                        "assignment_date": new_data["assignment_date"],
                        "address": new_data["address"],
                        "area_sqm": new_data["area_sqm"],
                        "land_category": new_data["land_category"],
                        "land_use": new_data["land_use"],
                        "cadastral_value": new_data["cadastral_value"],
                        "owner_name": new_data["owner_name"],
                        "owner_contacts": new_data["owner_contacts"]
                    }
                )
                self.refresh_all()
                self.on_plot_selected(item)

    def delete_plot(self, item):
        plot_id = int(item.text().split(".")[0])
        if QMessageBox.question(
            self, 
            "Удаление участка", 
            "Вы уверены, что хотите удалить этот участок?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.plot_manager.delete_plot(plot_id)
            self.update_plot_list()
            if self.current_plot_id == plot_id:
                self.current_plot_id = None
                self.add_harvest_btn.setEnabled(False)
                self.harvest_table.setRowCount(0)

    def optimized_close(self):

        if hasattr(self, 'status_checker'):
            self.status_checker.stop()
    
        if hasattr(self, 'map_widget'):
            self.map_widget.setHtml('')
            self.map_widget.page().deleteLater()
            self.map_widget.close()

        if hasattr(self, 'plot_manager') and hasattr(self.plot_manager, 'db'):
            self.plot_manager.db.close()

        cleanup_temp_files()
        
        if hasattr(self, 'harvest_table'):
            self.harvest_table.clearContents()
            self.harvest_table.setRowCount(0)
        
        if hasattr(self, 'plots_list'):
            self.plots_list.clear()
        
        if hasattr(self, 'tasks_table'):
            self.tasks_table.clearContents()
            self.tasks_table.setRowCount(0)

    def closeEvent(self, event):
        self.optimized_close()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.aboutToQuit.connect(cleanup_temp_files)
    sys.exit(app.exec_())