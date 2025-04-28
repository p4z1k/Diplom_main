from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QDialogButtonBox, QCheckBox, QDateEdit,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QWidget,
    QPushButton
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from map_widget import MapWidget
import math

class PlotWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Мастер добавления участка/поля")
        self.setMinimumSize(1000, 700)
        
        self.init_ui()
        self.init_map()
        
    def init_ui(self):
        main_layout = QHBoxLayout()
        
        form_panel = QWidget()
        form_layout = QVBoxLayout(form_panel)
        
        basic_group = QGroupBox("Основные данные")
        basic_layout = QFormLayout()
        
        self.plot_name_edit = QLineEdit()
        self.plot_name_edit.setPlaceholderText("Введите название участка")
        basic_layout.addRow("Наименование участка:", self.plot_name_edit)
        
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(['Собственный', 'Арендованный'])
        basic_layout.addRow("Тип участка:", self.plot_type_combo)
        
        self.cadastral_edit = QLineEdit()
        self.cadastral_edit.setPlaceholderText("Введите кадастровый номер")
        basic_layout.addRow("Кадастровый номер:", self.cadastral_edit)
        
        self.property_type_edit = QLineEdit("Земельный участок")
        self.property_type_edit.setReadOnly(True)
        self.property_type_check = QCheckBox("Изменить")
        self.property_type_check.toggled.connect(
            lambda checked: self.property_type_edit.setReadOnly(not checked)
        )
        type_layout = QHBoxLayout()
        type_layout.addWidget(self.property_type_edit)
        type_layout.addWidget(self.property_type_check)
        basic_layout.addRow("Вид объекта недвижимости:", type_layout)
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        basic_layout.addRow("Дата присвоения:", self.date_edit)
        
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Введите адрес/местоположение")
        basic_layout.addRow("Адрес:", self.address_edit)
        
        self.auto_area_check = QCheckBox("Автоматический расчет площади")
        self.auto_area_check.setChecked(True)
        self.auto_area_check.toggled.connect(self.toggle_area_input)
        
        self.area_sqm_edit = QDoubleSpinBox()
        self.area_sqm_edit.setSuffix(" кв.м")
        self.area_sqm_edit.setRange(0, 9999999)
        self.area_sqm_edit.setDecimals(2)
        self.area_sqm_edit.valueChanged.connect(self.update_hectares)
        
        self.area_ha_edit = QDoubleSpinBox()
        self.area_ha_edit.setSuffix(" га")
        self.area_ha_edit.setRange(0, 999999)
        self.area_ha_edit.setDecimals(4)
        self.area_ha_edit.valueChanged.connect(self.update_sqm)
        
        area_layout = QHBoxLayout()
        area_layout.addWidget(self.area_sqm_edit)
        area_layout.addWidget(self.area_ha_edit)
        
        basic_layout.addRow(self.auto_area_check)
        basic_layout.addRow("Площадь:", area_layout)
        
        basic_group.setLayout(basic_layout)
        form_layout.addWidget(basic_group)
        
        land_group = QGroupBox("Земельные характеристики")
        land_layout = QFormLayout()
        
        self.land_category_edit = QLineEdit("Земли сельскохозяйственного назначения")
        self.land_category_edit.setReadOnly(True)
        self.land_category_check = QCheckBox("Изменить")
        self.land_category_check.toggled.connect(
            lambda checked: self.land_category_edit.setReadOnly(not checked)
        )
        category_layout = QHBoxLayout()
        category_layout.addWidget(self.land_category_edit)
        category_layout.addWidget(self.land_category_check)
        land_layout.addRow("Категория земель:", category_layout)
        
        self.land_use_edit = QLineEdit("Для сельскохозяйственного производства")
        self.land_use_edit.setReadOnly(True)
        self.land_use_check = QCheckBox("Изменить")
        self.land_use_check.toggled.connect(
            lambda checked: self.land_use_edit.setReadOnly(not checked)
        )
        use_layout = QHBoxLayout()
        use_layout.addWidget(self.land_use_edit)
        use_layout.addWidget(self.land_use_check)
        land_layout.addRow("Разрешенное использование:", use_layout)
        
        self.cadastral_value_edit = QDoubleSpinBox()
        self.cadastral_value_edit.setSuffix(" руб.")
        self.cadastral_value_edit.setRange(0, 999999999)
        self.cadastral_value_edit.setDecimals(2)
        land_layout.addRow("Кадастровая стоимость:", self.cadastral_value_edit)
        
        land_group.setLayout(land_layout)
        form_layout.addWidget(land_group)
        
        owner_group = QGroupBox("Сведения о правообладателе")
        owner_layout = QFormLayout()
        
        self.owner_name_edit = QLineEdit()
        self.owner_name_edit.setPlaceholderText("ФИО правообладателя")
        owner_layout.addRow("ФИО:", self.owner_name_edit)
        
        self.owner_contacts_edit = QLineEdit()
        self.owner_contacts_edit.setPlaceholderText("Контактные данные")
        owner_layout.addRow("Контакты:", self.owner_contacts_edit)
        
        owner_group.setLayout(owner_layout)
        form_layout.addWidget(owner_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        form_layout.addWidget(buttons)
        
        self.map_panel = QWidget()
        map_layout = QVBoxLayout(self.map_panel)
        
        self.map_widget = MapWidget()
        self.map_widget.setMinimumSize(400, 400)
        
        self.draw_btn = QPushButton("Начать рисование границ")
        self.draw_btn.setCheckable(True)
        self.draw_btn.toggled.connect(self.toggle_drawing_mode)
        
        self.point_btn = QPushButton("Указать точку")
        self.point_btn.setCheckable(True)
        self.point_btn.toggled.connect(self.toggle_point_mode)
        
        self.save_coords_btn = QPushButton("Сохранить координаты")
        self.save_coords_btn.setEnabled(False)
        self.save_coords_btn.clicked.connect(self.save_coordinates)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.draw_btn)
        btn_layout.addWidget(self.point_btn)
        btn_layout.addWidget(self.save_coords_btn)
        
        map_layout.addLayout(btn_layout)
        map_layout.addWidget(self.map_widget)
        
        main_layout.addWidget(form_panel, stretch=2)
        main_layout.addWidget(self.map_panel, stretch=3)
        
        self.setLayout(main_layout)
        
    def init_map(self):
        self.coordinates = []
        self.drawing_mode = False
        self.point_mode = False
        self.current_polygon = None
        
    def toggle_drawing_mode(self, enabled):
        self.drawing_mode = enabled
        self.point_mode = False
        self.point_btn.setChecked(False)
        self.map_widget.toggle_drawing_mode(enabled)
        self.save_coords_btn.setEnabled(enabled)
        
        if not enabled:
            self.clear_map()
        
    def toggle_point_mode(self, enabled):
        self.point_mode = enabled
        self.drawing_mode = False
        self.draw_btn.setChecked(False)
        self.map_widget.toggle_drawing_mode(enabled)
        self.save_coords_btn.setEnabled(enabled)
        
        if not enabled:
            self.clear_map()
        
    def clear_map(self):
        if self.current_polygon:
            self.map_widget.page().runJavaScript(f"""
                if(window.currentPolygon) {{
                    map.geoObjects.remove(window.currentPolygon);
                    window.currentPolygon = null;
                }}
            """)
            self.current_polygon = None
        
    def save_coordinates(self):
        self.coordinates = self.map_widget.bridge.current_coordinates
        
        if self.point_mode and self.coordinates:
            lat, lng = self.coordinates[0]
            
            offset = 0.001
            self.coordinates = [
                [lat + offset, lng - offset],
                [lat + offset, lng + offset],
                [lat - offset, lng + offset],
                [lat - offset, lng - offset]
            ]
            
            if self.auto_area_check.isChecked():
                self.area_sqm_edit.setValue(100)
                self.area_ha_edit.setValue(0.01)
        
        elif self.drawing_mode and len(self.coordinates) >= 3:
            if self.auto_area_check.isChecked():
                area = self.calculate_area(self.coordinates)
                self.area_sqm_edit.setValue(area)
                self.area_ha_edit.setValue(area / 10000)

        self.display_saved_coordinates()
        
        self.draw_btn.setChecked(False)
        self.point_btn.setChecked(False)
        self.save_coords_btn.setEnabled(False)
        
    def display_saved_coordinates(self):
        if not self.coordinates or len(self.coordinates) < 3:
            return
            
        self.clear_map()
        
        js_coords = "[%s]" % ", ".join(
            "[%f, %f]" % (lat, lng) for lat, lng in self.coordinates
        )
        
        js_code = f"""
            if(window.currentPolygon) {{
                map.geoObjects.remove(window.currentPolygon);
            }}
            
            window.currentPolygon = new ymaps.Polygon([{js_coords}], {{}}, {{
                strokeColor: '#00AA00',
                fillColor: '#00FF0080',
                strokeWidth: 3
            }});
            
            map.geoObjects.add(window.currentPolygon);
            map.setBounds(window.currentPolygon.geometry.getBounds());
        """
        
        self.map_widget.page().runJavaScript(js_code)
        self.current_polygon = True 
        
    def calculate_area(self, coordinates):
        """Вычисляет площадь участка по координатам (в кв. метрах)"""
        if len(coordinates) < 3:
            return 0.0
            
        area = 0.0
        n = len(coordinates)
        
        for i in range(n):
            j = (i + 1) % n
            lat1, lon1 = coordinates[i]
            lat2, lon2 = coordinates[j]
            
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            area += (lon2_rad - lon1_rad) * (2 + math.sin(lat1_rad) + math.sin(lat2_rad))
        
        earth_radius = 6371000
        area = abs(area * earth_radius ** 2 / 2)
        
        return area
        
    def toggle_area_input(self, checked):
        self.area_sqm_edit.setEnabled(not checked)
        self.area_ha_edit.setEnabled(not checked)
        
    def update_hectares(self):
        if not self.auto_area_check.isChecked():
            self.area_ha_edit.setValue(self.area_sqm_edit.value() / 10000)
        
    def update_sqm(self):
        if not self.auto_area_check.isChecked():
            self.area_sqm_edit.setValue(self.area_ha_edit.value() * 10000)
            
    def get_data(self):
        return {
            "name": self.plot_name_edit.text(),
            "plot_type": self.plot_type_combo.currentText(),
            "cadastral_number": self.cadastral_edit.text(),
            "property_type": self.property_type_edit.text(),
            "assignment_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "address": self.address_edit.text(),
            "area_sqm": self.area_sqm_edit.value(),
            "area_ha": self.area_ha_edit.value(),
            "land_category": self.land_category_edit.text(),
            "land_use": self.land_use_edit.text(),
            "cadastral_value": self.cadastral_value_edit.value(),
            "owner_name": self.owner_name_edit.text(),
            "owner_contacts": self.owner_contacts_edit.text(),
            "coordinates": self.coordinates
        }