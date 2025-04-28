import os
import logging
from PyQt5.QtCore import QUrl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MapLoader:
    def __init__(self):
        self.API_KEY = "718490f1-55ce-41d2-9cd3-3d7a5faed336"  
        self.template_file = "map_template.html"
        self.temp_file = "temp_map.html"

    def load_template(self):
        try:
            if os.path.exists(self.template_file):
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    return f.read().replace('{API_KEY}', self.API_KEY)
            return self._get_default_template()
        except Exception as e:
            logger.error(f"Ошибка загрузки шаблона: {e}")
            return self._get_default_template()

    def _get_default_template(self):
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Yandex Map</title>
    <script src="https://api-maps.yandex.ru/2.1/?apikey={self.API_KEY}&lang=ru_RU"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        #map {{ height: 100%; width: 100%; }}
    </style>
</head>
<body>
    <div id="map"></div>
</body>
</html>"""

    def create_temp_map(self, html_content):
        try:
            with open(self.temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return QUrl.fromLocalFile(os.path.abspath(self.temp_file))
        except Exception as e:
            logger.error(f"Ошибка создания временного файла: {e}")
            return QUrl()

    def cleanup(self):
        try:
            if os.path.exists(self.temp_file):
                os.remove(self.temp_file)
        except Exception as e:
            logger.error(f"Ошибка удаления временного файла: {e}")

    def inject_js(self, html_content, js_code):
        return html_content.replace("</body>", f"<script>{js_code}</script></body>")

def cleanup_temp_files():
    loader = MapLoader()
    loader.cleanup()