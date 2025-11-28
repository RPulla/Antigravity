import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QColorDialog, QComboBox, 
                             QSpinBox, QMainWindow, QStackedWidget)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette

class DigitalClockWidget(QWidget):
    # Signal to request returning to settings
    return_to_settings = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = {}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.colon_visible = True
        
        self.init_ui()
        
    def init_ui(self):
        self.setAutoFillBackground(True)
        
        layout = QVBoxLayout()
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)
        self.setLayout(layout)

    def start_clock(self, settings):
        self.settings = settings
        
        # Apply Colors
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.settings['bg_color'])
        self.setPalette(palette)
        
        palette = self.time_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, self.settings['text_color'])
        self.time_label.setPalette(palette)
        
        self.timer.start(500)
        self.setFocus() # Important to catch key events

    def stop_clock(self):
        self.timer.stop()

    def update_font_size(self, target_height, target_width, size_mode):
        # Calculate font size based on mode
        # All modes now use HEIGHT as base dimension
        if size_mode == 'Small':
            percentage = 0.30  # 30% - keeps reasonable size
        elif size_mode == 'Medium':
            percentage = 0.50  # 50% - increased from 45% for better visibility
        else:  # Full Screen
            percentage = 0.55  # 55% - gives ~90-93% width coverage
        
        # Always use height as base dimension
        pixel_size = int(target_height * percentage)
        
        # Get font family from settings, default to system font
        font_family = self.settings.get('font_family', 'Monospace')
        font = QFont(font_family)
        font.setPixelSize(pixel_size)
        self.time_label.setFont(font)

    def update_time(self):
        if not self.settings:
            return

        utc_now = datetime.utcnow()
        offset = self.settings.get('gmt_offset', 0)
        current_time = utc_now + timedelta(hours=offset)
        
        hours = current_time.strftime("%H")
        minutes = current_time.strftime("%M")
        
        # Get text color from settings
        text_color = self.settings.get('text_color', QColor('red')).name()
        
        # Use HTML to make colon blink without changing layout
        # The colon is always there, just changes between visible and transparent
        if self.colon_visible:
            colon_html = f'<span style="color:{text_color};">:</span>'
        else:
            colon_html = f'<span style="color:transparent;">:</span>'
            
        time_html = f'{hours}{colon_html}{minutes}'
        self.time_label.setText(time_html)
        self.colon_visible = not self.colon_visible

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.return_to_settings.emit()
        else:
            super().keyPressEvent(event)

class SettingsWidget(QWidget):
    start_clock_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.settings = {
            'bg_color': QColor('black'),
            'text_color': QColor('red'),
            'size': 'Full Screen',
            'gmt_offset': -3,
            'font_family': 'Monospace',
            'resolution': '1920x1080'  # Default resolution
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Digital Clock Settings")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Background Color
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background Color:"))
        self.bg_btn = QPushButton("Select Color")
        self.bg_btn.clicked.connect(self.choose_bg_color)
        self.update_color_btn(self.bg_btn, self.settings['bg_color'])
        bg_layout.addWidget(self.bg_btn)
        layout.addLayout(bg_layout)
        
        # Text Color
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text Color:"))
        self.text_btn = QPushButton("Select Color")
        self.text_btn.clicked.connect(self.choose_text_color)
        self.update_color_btn(self.text_btn, self.settings['text_color'])
        text_layout.addWidget(self.text_btn)
        layout.addLayout(text_layout)
        
        # Size Selection
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Clock Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(['Small', 'Medium', 'Full Screen'])
        self.size_combo.setCurrentText(self.settings['size'])
        self.size_combo.currentTextChanged.connect(self.set_size)
        size_layout.addWidget(self.size_combo)
        layout.addLayout(size_layout)
        
        # GMT Selection
        gmt_layout = QHBoxLayout()
        gmt_layout.addWidget(QLabel("GMT Offset:"))
        self.gmt_spin = QSpinBox()
        self.gmt_spin.setRange(-12, 14)
        self.gmt_spin.setValue(self.settings['gmt_offset'])
        self.gmt_spin.valueChanged.connect(self.set_gmt)
        gmt_layout.addWidget(self.gmt_spin)
        layout.addLayout(gmt_layout)
        
        # Font Family Selection
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Family:"))
        self.font_combo = QComboBox()
        # Fonts commonly available on Raspberry Pi
        self.font_combo.addItems(['Monospace', 'Liberation Mono', 'DejaVu Sans Mono', 
                                   'Courier New', 'FreeMono', 'Ubuntu Mono'])
        self.font_combo.setCurrentText(self.settings['font_family'])
        self.font_combo.currentTextChanged.connect(self.set_font)
        font_layout.addWidget(self.font_combo)
        layout.addLayout(font_layout)
        
        # Monitor Resolution Selection
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Monitor Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            '1920x1080',
            '1680x1050',
            '1600x900',
            '1440x900',
            '1366x768',
            '1360x768',
            '1280x1024',
            '1280x960',
            '1280x800',
            '1280x720',
            '1280x600'
        ])
        self.resolution_combo.setCurrentText(self.settings['resolution'])
        self.resolution_combo.currentTextChanged.connect(self.set_resolution)
        resolution_layout.addWidget(self.resolution_combo)
        layout.addLayout(resolution_layout)
        
        # Start Button
        self.start_btn = QPushButton("Start Clock")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.start_btn.clicked.connect(self.on_start)
        layout.addWidget(self.start_btn)
        
        self.setLayout(layout)

    def update_color_btn(self, btn, color):
        btn.setStyleSheet(f"background-color: {color.name()}; color: {'white' if color.lightness() < 128 else 'black'}")

    def choose_bg_color(self):
        color = QColorDialog.getColor(self.settings['bg_color'], self, "Select Background Color")
        if color.isValid():
            self.settings['bg_color'] = color
            self.update_color_btn(self.bg_btn, color)

    def choose_text_color(self):
        color = QColorDialog.getColor(self.settings['text_color'], self, "Select Text Color")
        if color.isValid():
            self.settings['text_color'] = color
            self.update_color_btn(self.text_btn, color)

    def set_size(self, text):
        self.settings['size'] = text

    def set_gmt(self, value):
        self.settings['gmt_offset'] = value

    def set_font(self, text):
        self.settings['font_family'] = text

    def set_resolution(self, text):
        self.settings['resolution'] = text

    def on_start(self):
        self.start_clock_signal.emit(self.settings)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Clock App")
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.settings_widget = SettingsWidget()
        self.clock_widget = DigitalClockWidget()
        
        self.stacked_widget.addWidget(self.settings_widget)
        self.stacked_widget.addWidget(self.clock_widget)
        
        # Connect signals
        self.settings_widget.start_clock_signal.connect(self.show_clock)
        self.clock_widget.return_to_settings.connect(self.show_settings)
        
        self.show_settings()

    def show_settings(self):
        self.clock_widget.stop_clock()
        self.showNormal()
        self.resize(400, 500) # Default settings size
        self.stacked_widget.setCurrentWidget(self.settings_widget)

    def show_clock(self, settings):
        self.stacked_widget.setCurrentWidget(self.clock_widget)
        
        # Parse selected resolution from settings
        resolution = settings.get('resolution', '1920x1080')
        width_str, height_str = resolution.split('x')
        screen_width = int(width_str)
        screen_height = int(height_str)
        
        size_mode = settings['size']
        if size_mode == 'Full Screen':
            self.showFullScreen()
        else:
            self.showNormal()
            if size_mode == 'Small':
                self.resize(400, 200)
            elif size_mode == 'Medium':
                self.resize(800, 400)
        
        # Force layout update to get correct dimensions
        QApplication.processEvents()
        
        # Start clock logic and set font size based on SELECTED resolution
        # This uses the user's manually selected monitor resolution
        self.clock_widget.start_clock(settings)
        self.clock_widget.update_font_size(screen_height, screen_width, settings['size'])
        self.clock_widget.setFocus() # Ensure it gets key events

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
