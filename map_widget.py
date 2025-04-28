from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtWebChannel import QWebChannel
import os

class MapBridge(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_coordinates = []

    @pyqtSlot(float, float)
    def add_point(self, lat, lng):
        self.current_coordinates.append([lat, lng])

class MapWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.API_KEY = "718490f1-55ce-41d2-9cd3-3d7a5faed336"
        self.bridge = MapBridge()
        self.drawing_mode = False
        self.init_map()
        
        #отладчик ебаной карты
        os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'

    def init_map(self):
        self.channel = QWebChannel()
        self.channel.registerObject('bridge', self.bridge)
        self.page().setWebChannel(self.channel)

        html_content = self._load_template()
        js_code = self._get_map_js()
        html_content = html_content.replace("</script>", f"{js_code}</script>")
        
        self.setHtml(html_content, QUrl("about:blank"))

    def _load_template(self):
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Yandex Map</title>
    <script src="https://api-maps.yandex.ru/2.1/?apikey={self.API_KEY}&lang=ru_RU"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        #map {{
            width: 100%;
            height: 100vh;
            margin: 0;
            padding: 0;
        }}
        .map-status {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: white;
            padding: 5px 10px;
            z-index: 1000;
            border-radius: 3px;
            box-shadow: 0 0 5px rgba(0,0,0,0.3);
        }}
    </style>
</head>
<body>
    <div class="map-status">Инициализация карты...</div>
    <div id="map"></div>
    <script>
        // JavaScript code will be injected here
    </script>
</body>
</html>"""

    def _get_map_js(self):
        return """
        var map;
        var polygon;
        var clickPoints = [];
        var searchControl;
        
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.bridge = channel.objects.bridge;
        });
        
        ymaps.ready(init);
        
        function init() {
            document.querySelector('.map-status').textContent = 'Загрузка карты...';
            
            map = new ymaps.Map('map', {
                center: [52.982869, 37.397889],
                zoom: 13,
                controls: ['zoomControl', 'typeSelector']
            });

            searchControl = new ymaps.control.SearchControl({
                options: {
                    provider: 'yandex#search',
                    noPlacemark: true,
                    placeholderContent: 'Поиск адреса...',
                    size: 'large'
                }
            });
            
            map.controls.add(searchControl, { float: 'left' });

            searchControl.events.add('resultselect', function(e) {
                var index = e.get('index');
                searchControl.getResult(index).then(function(res) {
                    var coordinates = res.geometry.getCoordinates();
                    map.panTo(coordinates, {
                        flying: true,
                        checkZoomRange: true
                    });
                });
            });

            map.events.add('click', function(e) {
                if(window.drawingMode && window.bridge) {
                    var coords = e.get('coords');
                    clickPoints.push(coords);
                    bridge.add_point(coords[0], coords[1]);
                    
                    if(polygon) map.geoObjects.remove(polygon);
                    polygon = new ymaps.Polygon([clickPoints], {}, {
                        strokeColor: '#FF0000',
                        fillColor: '#FF000080'
                    });
                    map.geoObjects.add(polygon);
                }
            });
            
            document.querySelector('.map-status').textContent = 'Карта готова';
            setTimeout(() => {
                document.querySelector('.map-status').style.display = 'none';
            }, 1000);
        }
        
        function drawPlot(coordinates) {
            if(polygon) map.geoObjects.remove(polygon);
            polygon = new ymaps.Polygon([coordinates], {}, {
                strokeColor: '#00FF00',
                fillColor: '#00FF0080'
            });
            map.geoObjects.add(polygon);
            map.setBounds(polygon.geometry.getBounds());
        }
        
        window.drawingMode = false;
        """

    def draw_existing_plot(self, coordinates):
        if coordinates:
            self.page().runJavaScript(f"drawPlot({coordinates})")

    def toggle_drawing_mode(self, enabled):
        self.drawing_mode = enabled
        self.page().runJavaScript(f"window.drawingMode = {str(enabled).lower()};")
        
        if not enabled:
            self.bridge.current_coordinates = []
            self.page().runJavaScript("""
                if(polygon) {
                    map.geoObjects.remove(polygon);
                    polygon = null;
                }
                clickPoints = [];
            """)