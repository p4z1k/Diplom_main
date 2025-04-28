import json
from datetime import datetime
from typing import List, Dict, Optional
from database_manager import DatabaseManager

class LandPlotManager:
    def __init__(self, db_path="full_data.db"):
        self.db = DatabaseManager(db_path)
        self.status_settings = {
            "default_flow": ["Засеяно", "Требует удобрения", "Готов к сбору"],
            "status_times": {
                "Засеяно": 5,
                "Требует удобрения": 3
            }
        }
        self.load_status_settings()

    def add_plot(self, name, coordinates, area, plot_type, status, additional_data=None):
        now = datetime.now().isoformat()
    
        self.db.execute("""
            INSERT INTO plots (
                name, coordinates, area, type, status, 
                cadastral_number, property_type, address,
                land_category, land_use, cadastral_value,
                owner_name, owner_contacts, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            json.dumps(coordinates),
            area,
            plot_type,
            status,
            additional_data.get("cadastral_number", ""),
            additional_data.get("property_type", ""),
            additional_data.get("address", ""),
            additional_data.get("land_category", ""),
            additional_data.get("land_use", ""),
            additional_data.get("cadastral_value", 0),
            additional_data.get("owner_name", ""),
            additional_data.get("owner_contacts", ""),
            now,
            now
        ))

    def get_all_plots(self, sort_key: str = 'name', 
                      filter_type: str = None, 
                      search_query: str = None) -> List[Dict]:
        query = "SELECT * FROM plots WHERE 1=1"
        params = []

        if filter_type:
            query += " AND type = ?"
            params.append(filter_type)
        if search_query:
            query += " AND LOWER(name) LIKE ?"
            params.append(f"%{search_query.lower()}%")

        query += f" ORDER BY {sort_key}"

        plots = self.db.fetch_all(query, tuple(params))
        for plot in plots:
            plot["coordinates"] = json.loads(plot["coordinates"])
            plot["auto_status"] = bool(plot["auto_status"])
        return plots

    def get_plot_by_id(self, plot_id: int) -> Optional[Dict]:
        plot = self.db.fetch_one("SELECT * FROM plots WHERE id = ?", (plot_id,))
        if plot:
            plot["coordinates"] = json.loads(plot["coordinates"])
            plot["auto_status"] = bool(plot["auto_status"])
        return plot

    def update_plot(self, plot_id: int, **kwargs):
        keys = []
        values = []
        for key, value in kwargs.items():
            if key == "coordinates":
                value = json.dumps(value)
            keys.append(f"{key} = ?")
            values.append(value)
        keys.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(plot_id)

        self.db.execute(f"""
            UPDATE plots SET {', '.join(keys)} WHERE id = ?
        """, tuple(values))
        return True

    def delete_plot(self, plot_id: int) -> bool:
        self.db.execute("DELETE FROM plots WHERE id = ?", (plot_id,))
        return True

    def update_plot_status(self, plot_id: int, new_status: str):
        now = datetime.now().isoformat()
        self.db.execute("""
            UPDATE plots SET status = ?, status_changed = ?, updated_at = ?
            WHERE id = ?
        """, (new_status, now, now, plot_id))
        return True

    def add_harvest_record(self, plot_id: int, date: str, culture: str, amount: float):
        self.db.execute("""
            INSERT INTO harvests (plot_id, date, culture, amount)
            VALUES (?, ?, ?, ?)
        """, (plot_id, date, culture, amount))
        return True

    def get_harvests_for_plot(self, plot_id: int) -> List[Dict]:
        return self.db.fetch_all("SELECT * FROM harvests WHERE plot_id = ?", (plot_id,))

    def get_next_status(self, current_status: str) -> Optional[str]:
        flow = self.status_settings["default_flow"]
        try:
            idx = flow.index(current_status)
            return flow[idx+1] if idx+1 < len(flow) else None
        except ValueError:
            return None

    def get_status_wait_time(self, status: str) -> int:
        return self.status_settings["status_times"].get(status, 0)

    def load_status_settings(self):
        default_flow = self.db.fetch_one("SELECT value FROM status_settings WHERE key = 'default_flow'")
        status_times = self.db.fetch_one("SELECT value FROM status_settings WHERE key = 'status_times'")

        if default_flow:
            self.status_settings["default_flow"] = json.loads(default_flow["value"])
        if status_times:
            self.status_settings["status_times"] = json.loads(status_times["value"])

    def save_status_settings(self):
        self.db.execute("""
            INSERT INTO status_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, ("default_flow", json.dumps(self.status_settings["default_flow"])))

        self.db.execute("""
            INSERT INTO status_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, ("status_times", json.dumps(self.status_settings["status_times"])))
