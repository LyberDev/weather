import sys
import requests
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QStackedWidget, QGraphicsOpacityEffect, 
                             QLineEdit, QComboBox, QPushButton)
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QFontMetrics

LANG_MAP = {
    "Русский": {"hum": "ВЛАЖНОСТЬ", "wind": "ВЕТЕР", "ms": "М/С", "api": "ru", "err": "Город не найден!"},
    "English": {"hum": "HUMIDITY", "wind": "WIND", "ms": "M/S", "api": "en", "err": "City not found!"},
    "Deutsch": {"hum": "FEUCHTIGKEIT", "wind": "WIND", "ms": "M/S", "api": "de", "err": "Stadt nicht gefunden!"}
}

class StartDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #0A0F14; border: 2px solid #00F2FF;")
        self.setFixedSize(400, 280)
        self.selected_lang = "Русский"
        self.selected_city = "Pskov"
        self.confirmed = False

        layout = QVBoxLayout(self)
        
        title = QLabel("SETTINGS / НАСТРОЙКИ")
        title.setStyleSheet("color: #00F2FF; border: none; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.lang_box = QComboBox()
        self.lang_box.addItems(["Русский", "English", "Deutsch"])
        self.lang_box.setStyleSheet("color: white; background: #1A1F24; padding: 5px;")
        layout.addWidget(self.lang_box)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("City / Город...")
        self.city_input.setStyleSheet("color: white; background: #1A1F24; padding: 5px; border: 1px solid #39FF14;")
        layout.addWidget(self.city_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #FF3131; border: none; font-size: 12px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        btn = QPushButton("START / ЗАПУСК")
        btn.setStyleSheet("background-color: #39FF14; color: black; font-weight: bold; padding: 10px;")
        btn.clicked.connect(self.validate_and_finish)
        layout.addWidget(btn)

    def validate_and_finish(self):
        city = self.city_input.text().strip()
        lang = self.lang_box.currentText()
        if not city:
            self.error_label.setText(LANG_MAP[lang]["err"])
            return

        try:
            api_key = "8c58a6cb6d44a61fec5fc8cd1ae2daa0"
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
            res = requests.get(url, timeout=3).json()
            
            if res.get("cod") == 200:
                self.selected_lang = lang
                self.selected_city = city
                self.confirmed = True
                self.close()
            else:
                self.error_label.setText(LANG_MAP[lang]["err"])
        except:
            self.error_label.setText("Connection Error / Ошибка сети")

class GlowLabel(QLabel):
    def __init__(self, color, font_size_div):
        super().__init__()
        self.glow_color = QColor(color)
        self.font_size_div = font_size_div
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w = self.window().width()
        base_size = int(w / self.font_size_div)
        font = QFont("Verdana", base_size, QFont.Weight.Bold)
        if ":" in self.text(): font = QFont("Courier New", base_size, QFont.Weight.Bold)
        
        metrics = QFontMetrics(font)
        text_lines = self.text().split('\n')
        max_text_w = max([metrics.horizontalAdvance(line) for line in text_lines]) if text_lines else 0
        while max_text_w > (self.width() * 0.9) and base_size > 10:
            base_size -= 2
            font.setPointSize(base_size)
            metrics = QFontMetrics(font)
            max_text_w = max([metrics.horizontalAdvance(line) for line in text_lines])
            
        painter.setFont(font)
        base_color = QColor(self.glow_color)
        for offset in range(4, 0, -1):
            base_color.setAlpha(30 // offset)
            painter.setPen(base_color)
            for dx, dy in [(-offset,0), (offset,0), (0,-offset), (0,offset)]:
                painter.drawText(self.rect().adjusted(dx, dy, dx, dy), self.alignment(), self.text())
        
        self.glow_color.setAlpha(255)
        painter.setPen(self.glow_color)
        painter.drawText(self.rect(), self.alignment(), self.text())
        painter.end()

class WeatherDashboard(QWidget):
    def __init__(self, city, lang_key):
        super().__init__()
        self.city = city
        self.lang_key = lang_key
        self.api_key = "8c58a6cb6d44a61fec5fc8cd1ae2daa0"
        self.weather_data = {"temp": "--°", "desc": "", "details": ""}
        self.drag_pos = QPoint()
        self.init_ui()
        self.update_weather()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(1000, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()

        self.screen_temp = GlowLabel("#00F2FF", 10) 
        self.screen_time = GlowLabel("#FFFFFF", 7) 
        self.screen_details = GlowLabel("#39FF14", 16) 

        self.stack.addWidget(self.screen_temp)
        self.stack.addWidget(self.screen_time)
        self.stack.addWidget(self.screen_details)

        layout.addWidget(self.stack)
        self.opacity_effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self.opacity_effect)

        self.display_timer = QTimer(self); self.display_timer.timeout.connect(self.fade_out_animation); self.display_timer.start(10000)
        self.clock_timer = QTimer(self); self.clock_timer.timeout.connect(self.update_clock); self.clock_timer.start(1000)
        self.api_timer = QTimer(self); self.api_timer.timeout.connect(self.update_weather); self.api_timer.start(600000)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        painter.end()

    def update_weather(self):
        try:
            l = LANG_MAP[self.lang_key]
            url = f"http://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}&units=metric&lang={l['api']}"
            res = requests.get(url, timeout=5).json()
            if res.get("cod") == 200:
                temp = f"{round(res['main']['temp'])}°"
                desc = res['weather'][0]['description'].upper()
                details = f"{l['hum']}: {res['main']['humidity']}%\n{l['wind']}: {res['wind']['speed']} {l['ms']}"
                self.screen_temp.setText(f"{temp}\n{desc}")
                self.screen_details.setText(details)
        except: pass

    def update_clock(self): self.screen_time.setText(datetime.now().strftime("%H:%M:%S"))

    def fade_out_animation(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(600); self.anim.setStartValue(1.0); self.anim.setEndValue(0.0)
        self.anim.finished.connect(lambda: self.switch_screen()); self.anim.start()

    def switch_screen(self):
        self.stack.setCurrentIndex((self.stack.currentIndex() + 1) % 3)
        self.anim_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_in.setDuration(600); self.anim_in.setStartValue(0.0); self.anim_in.setEndValue(1.0); self.anim_in.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape: self.close()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen(): self.showNormal()
            else: self.showFullScreen()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = StartDialog()
    dialog.show()
    app.exec()
    if dialog.confirmed:
        window = WeatherDashboard(dialog.selected_city, dialog.selected_lang)
        window.show()
        sys.exit(app.exec())
