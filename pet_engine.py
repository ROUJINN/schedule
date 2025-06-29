# pet_engine.py
from PySide6.QtCore import Qt, QPoint, QTimer, QSize, Property, Signal, QObject
from PySide6.QtGui import QMovie, QPainter, QColor, QIcon
from PySide6.QtWidgets import (QWidget, QMenu, QSystemTrayIcon, 
                              QGraphicsOpacityEffect, QApplication)
import os
import json


#TODO:换图标,增加sleep.gif
T = 60 #几分钟自动减少hp

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
        # --- 新增：心情与动画管理 ---
        self.last_active_timer = QTimer()
        self.last_active_timer.setInterval(3 * 3600 * 1000)  # 3小时
        self.last_active_timer.timeout.connect(self.set_sleep)
        self.last_active_timer.start()
        self.is_sleeping = False
        self.installEventFilter(self)
        self.update_pet_animation()
        self.state.hp_changed.connect(self.update_pet_animation)

    def init_pet(self):
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 200)

        # 宠物动画
        self.movie = QMovie("pet/happy.gif")
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
        exit_action = menu.addAction("退出程序")
        exit_action.triggered.connect(QApplication.quit)
        
        self.tray.setContextMenu(menu)
        self.tray.show()

    def init_hp_timer(self):
        # 每小时自动减少HP
        self.hp_timer = QTimer()
        self.hp_timer.timeout.connect(self.auto_decrease_hp)
        self.hp_timer.start(1000*T)  # 每分钟,可以修改T

    def auto_decrease_hp(self):
        if self.state.hp > 5:
            self.state.hp = max(5, self.state.hp - 5)
    def increase_hp(self, amount):
        self.hp = min(100, self.hp + amount)
        
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # --- HP条居中 ---
        bar_width = 200
        bar_height = 8
        bar_x = (self.width() - bar_width) // 2
        bar_y = 10

        # --- HP条颜色 ---
        hp = self.state.hp
        if hp > 60:
            color = QColor(0, 200, 0, 180)      # 绿色
        elif hp > 30:
            color = QColor(255, 200, 0, 180)    # 黄色
        elif hp > 5:
            color = QColor(255, 0, 0, 180)      # 红色
        else:
            color = QColor(120, 0, 0, 220)      # 深红色

        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(10,10, int(bar_width * (hp / 100)), 8)

        # 绘制宠物动画
        if self.movie.state() == QMovie.Running:
            current = self.movie.currentPixmap()
            painter.drawPixmap(0, 20, current.scaled(200, 180))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            menu = QMenu(self)
            action_hide = menu.addAction("隐藏到托盘")
            action_hide.triggered.connect(self.hide)
            action_show = menu.addAction("显示主窗口")
            action_show.triggered.connect(self.show_main_window)
            menu.addSeparator()
            action_exit = menu.addAction("退出程序")
            action_exit.triggered.connect(QApplication.quit)
            menu.exec(event.globalPosition().toPoint())

    def show_main_window(self):
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "MainWindow":
                widget.showNormal()
                widget.raise_()
                widget.activateWindow()
                break

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

    # --- 新增：心情与动画切换 ---
    def update_pet_animation(self):
        if self.is_sleeping:
            self.set_movie("pet/sleep.gif")
        elif self.state.hp > 60:
            self.set_movie("pet/happy.gif")
        else:
            self.set_movie("pet/angry.gif")

    def set_movie(self, path):
        if self.movie.fileName() != path:
            self.movie.stop()
            self.movie.setFileName(path)
            self.movie.start()

    def set_sleep(self):
        self.is_sleeping = True
        self.update_pet_animation()

    def eventFilter(self, obj, event):
        # 只要有用户操作就重置计时器
        if event.type() in (
            2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 18, 24, 25, 31
        ):  # 常见事件类型
            self.last_active_timer.start()
            if self.is_sleeping:
                self.is_sleeping = False
                self.update_pet_animation()
        return super().eventFilter(obj, event)