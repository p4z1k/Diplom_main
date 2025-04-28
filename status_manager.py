from PyQt5.QtCore import QObject, pyqtSignal, QDate
from datetime import datetime

class StatusManager(QObject):
    status_updated = pyqtSignal()

    def __init__(self, plot_manager):
        super().__init__()
        self.plot_manager = plot_manager

    def calculate_days_left(self, plot):
        status = plot.get('status')
        changed = plot.get('status_changed')

        if not status or not changed or status not in self.plot_manager.status_settings["status_times"]:
            return "∞"

        wait_days = self.plot_manager.get_status_wait_time(status)
        if wait_days <= 0:
            return "∞"

        changed_date = QDate.fromString(changed[:10], "yyyy-MM-dd")
        days_passed = changed_date.daysTo(QDate.currentDate())
        days_left = max(0, wait_days - days_passed)

        return days_left

    def get_task_state(self, plot, days_left):
        if days_left == "∞":
            return "Без срока"

        if days_left == 0:
            return "Просрочено"

        if days_left <= 2:
            return f"Срочно! Осталось {days_left} дн."

        return f"Активно ({days_left} дн.)"

    def restart_status_cycle(self, plot):
        if not self.plot_manager.status_settings["default_flow"]:
            return

        first_status = self.plot_manager.status_settings["default_flow"][0]

        if plot.get('culture'):
            self.plot_manager.add_harvest_record(
                plot['id'],
                datetime.now().isoformat()[:10],
                plot['culture'],
                0
            )

        self.plot_manager.update_plot_status(plot['id'], first_status)
        self.status_updated.emit()

    def complete_task(self, plot):
        current_status = plot.get('status')
        next_status = self.plot_manager.get_next_status(current_status)

        if next_status:
            self.plot_manager.update_plot_status(plot['id'], next_status)
            self.status_updated.emit()
            return True

        if current_status in self.plot_manager.status_settings["default_flow"]:
            self.restart_status_cycle(plot)
            return True

        return False
