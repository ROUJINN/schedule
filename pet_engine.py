# pet_engine.py
import json
import os
from PySide6.QtCore import Qt, QPoint, QTimer, QSize, Property, Signal, QObject
from PySide6.QtGui import QMovie, QPainter, QColor, QIcon
from PySide6.QtWidgets import (QWidget, QMenu, QSystemTrayIcon, 
                              QGraphicsOpacityEffect, QApplication)

class PetState(QObject):
    """宠物状态管理"""
    hp_changed = Signal(int)
    mood_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.state_file = "data/pet_state.json"
        self._hp = 100
        self._food = 100
        self._mood = "normal"
        self.load_state()

    @Property(int, notify=hp_changed)
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        if self._hp != value:
            self._hp = max(0, min(100, value))
            self.hp_changed.emit(self._hp)
            self.save_state()

    @Property(int)
    def food(self):
        return self._food

    @food.setter
    def food(self, value):
        self._food = max(0, min(100, value))
        self.save_state()

    @Property(str, notify=mood_changed)
    def mood(self):
        return self._mood

    @mood.setter
    def mood(self, value):
        if self._mood != value:
            self._mood = value
            self.mood_changed.emit(value)
            self.save_state()

    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self._hp = data.get('hp', 100)
                    self._food = data.get('food', 100)
                    self._mood = data.get('mood', 'normal')
        except Exception as e:
            print(f"加载宠物状态失败: {e}")

    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    'hp': self._hp,
                    'food': self._food,
                    'mood': self._mood
                }, f)
        except Exception as e:
            print(f"保存宠物状态失败: {e}")

class DesktopPet(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.init_pet()
        self.init_tray()
        self.init_hp_timer()

    def init_pet(self):
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 200)

        # 宠物动画
        self.movie = QMovie("pet/default.gif")
        self.movie.frameChanged.connect(self.update)
        self.movie.start()

        # 拖拽相关
        self.drag_pos = QPoint()
        self.setCursor(Qt.OpenHandCursor)

    def init_tray(self):
        # 系统托盘
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("pet/tray_icon.png"))
        self.tray.activated.connect(self.toggle_visibility)
        
        menu = QMenu()
        show_action = menu.addAction("显示宠物")
        show_action.triggered.connect(self.show_normal)
        menu.addSeparator()
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(QApplication.quit)
        
        self.tray.setContextMenu(menu)
        self.tray.show()

    def init_hp_timer(self):
        # 每小时自动减少HP
        self.hp_timer = QTimer()
        self.hp_timer.timeout.connect(self.auto_decrease_hp)
        self.hp_timer.start(3600000)  # 1小时

    def auto_decrease_hp(self):
        self.state.hp = max(0, self.state.hp - 5)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制HP条
        painter.setBrush(QColor(255, 0, 0, 100))
        painter.drawRect(10, 10, 180 * (self.state.hp / 100), 8)
        
        # 绘制宠物动画
        if self.movie.state() == QMovie.Running:
            current = self.movie.currentPixmap()
            painter.drawPixmap(0, 20, current.scaled(200, 180))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)

    def toggle_visibility(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.setVisible(not self.isVisible())

    def show_normal(self):
        self.show()
        self.setWindowState(Qt.WindowNoState)