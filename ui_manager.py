#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import sys
import logging
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QDateEdit, QTimeEdit, QTextEdit,
    QMessageBox, QTabWidget, QScrollArea, QCalendarWidget, QDialog,
    QGridLayout, QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QFrame, QApplication, QStyle, QMenu,
    QInputDialog, QFileDialog, QToolBar, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, QTime, QDateTime, Slot, QSize, QRect, Signal
from PySide6.QtGui import QIcon, QColor, QPalette, QFont, QAction, QPainter, QPen, QBrush

# 导入项目其他模块
from my_schedule import Schedule
from reminder import Reminder
from pet_engine import PetState, DesktopPet

# 导入Excel导出相关库
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import json

class CustomCalendarWidget(QCalendarWidget):
    """自定义日历控件，支持高亮有任务的日期"""
    
    def __init__(self, parent=None, schedule_manager=None):
        super().__init__(parent)
        self.schedule_manager = schedule_manager
        self.dates_with_tasks = set()  # 存储有任务的日期
        self.initUI()
        
    def initUI(self):
        """初始化UI样式"""
        # 设置更现代化的样式
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #F5F5F5;
            }
            QCalendarWidget QToolButton {
                color: #333333;
                border: 1px solid transparent;
                background-color: transparent;
                padding: 6px;
                font-weight: bold;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #E3F2FD;
                border: 1px solid #BBDEFB;
                border-radius: 2px;
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #E0E0E0;
            }
            QCalendarWidget QSpinBox {
                border: 1px solid #E0E0E0;
                background-color: white;
                selection-background-color: #BBDEFB;
            }
            QCalendarWidget QAbstractItemView:enabled {
                selection-background-color: #E3F2FD;
                selection-color: #333333;
            }
        """)
        
        # 设置周末不显示为红色
        self.setWeekdayTextFormat(Qt.Saturday, self.weekdayTextFormat(Qt.Monday))
        self.setWeekdayTextFormat(Qt.Sunday, self.weekdayTextFormat(Qt.Monday))
        
    def update_dates_with_tasks(self):
        """更新有任务的日期列表"""
        if not self.schedule_manager:
            return
            
        # 获取当前显示的月份的第一天和最后一天
        year = self.yearShown()
        month = self.monthShown()
        first_day = QDate(year, month, 1)
        last_day = QDate(year, month, first_day.daysInMonth())
        
        # 获取这个月的所有任务
        from_date = first_day.toString("yyyy-MM-dd")
        to_date = last_day.toString("yyyy-MM-dd")
        tasks = self.schedule_manager.get_tasks(from_date=from_date, to_date=to_date)
        
        # 存储有任务的日期
        self.dates_with_tasks.clear()
        for task in tasks:
            try:
                task_date = QDate.fromString(task["due_date"], "yyyy-MM-dd")
                self.dates_with_tasks.add(task_date.toString("yyyy-MM-dd"))
            except Exception:
                continue
                
        # 更新日历显示
        self.updateCells()
        
    def paintCell(self, painter, rect, date):
        """重写绘制单元格方法，为有任务的日期添加不同的背景色"""
        # 调用父类方法先绘制默认外观
        super().paintCell(painter, rect, date)
        
        # 检查该日期是否有任务
        if date.toString("yyyy-MM-dd") in self.dates_with_tasks:
            # 使用浅蓝色背景突出显示有任务的日期
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(217, 232, 252))  # 浅蓝色
            painter.setOpacity(0.6)  # 设置透明度
            painter.drawRect(rect)
            painter.restore()

class TaskDialog(QDialog):
    """任务详情对话框，用于添加/编辑任务"""
    
    def __init__(self, parent=None, task=None):
        """
        初始化任务对话框
        
        Args:
            parent: 父窗口
            task: 如果是编辑现有任务，传入任务数据
        """
        super().__init__(parent)
        self.task = task
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题
        if self.task:
            self.setWindowTitle("编辑任务")
        else:
            self.setWindowTitle("添加新任务")
            
        self.setMinimumWidth(400)
        
        # 创建布局
        main_layout = QVBoxLayout()
        form_layout = QGridLayout()
        
        # 标题
        self.title_label = QLabel("任务:")
        self.title_input = QLineEdit()
        form_layout.addWidget(self.title_label, 0, 0)
        form_layout.addWidget(self.title_input, 0, 1)
        
        # 描述
        self.desc_label = QLabel("描述:")
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        form_layout.addWidget(self.desc_label, 1, 0)
        form_layout.addWidget(self.desc_input, 1, 1)
        
        # 类别
        self.category_label = QLabel("类别:")
        self.category_input = QComboBox()
        self.category_input.addItems([Schedule.WORK, Schedule.STUDY, Schedule.LIFE, Schedule.OTHER])
        form_layout.addWidget(self.category_label, 2, 0)
        form_layout.addWidget(self.category_input, 2, 1)
        
        # 优先级
        self.priority_label = QLabel("优先级:")
        self.priority_input = QComboBox()
        self.priority_input.addItems([Schedule.HIGH, Schedule.MEDIUM, Schedule.LOW])
        form_layout.addWidget(self.priority_label, 3, 0)
        form_layout.addWidget(self.priority_input, 3, 1)
        
        # 截止日期
        self.due_date_label = QLabel("截止日期:")
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.due_date_label, 4, 0)
        form_layout.addWidget(self.due_date_input, 4, 1)
        
        # 开始时间
        self.start_time_label = QLabel("开始时间:")
        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime(9, 0))
        form_layout.addWidget(self.start_time_label, 5, 0)
        form_layout.addWidget(self.start_time_input, 5, 1)
        
        # 结束时间
        self.end_time_label = QLabel("结束时间:")
        self.end_time_input = QTimeEdit()
        self.end_time_input.setTime(QTime(10, 0))
        form_layout.addWidget(self.end_time_label, 6, 0)
        form_layout.addWidget(self.end_time_input, 6, 1)
        
        # 重复任务
        self.repeat_label = QLabel("重复:")
        self.repeat_input = QComboBox()
        self.repeat_input.addItems(["不重复", "每天", "每周", "每月"])
        form_layout.addWidget(self.repeat_label, 7, 0)
        form_layout.addWidget(self.repeat_input, 7, 1)
        
        # 提醒
        self.reminder_label = QLabel("提醒:")
        self.reminder_check = QCheckBox("启用提醒")
        self.reminder_time = QSpinBox()
        self.reminder_time.setRange(1, 60)
        self.reminder_time.setValue(15)
        self.reminder_time.setSuffix(" 分钟前")
        
        reminder_layout = QHBoxLayout()
        reminder_layout.addWidget(self.reminder_check)
        reminder_layout.addWidget(self.reminder_time)
        
        form_layout.addWidget(self.reminder_label, 8, 0)
        form_layout.addLayout(reminder_layout, 8, 1)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("取消")
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        # 连接信号
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        # 添加到主布局
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 填充现有任务数据（如果是编辑）
        if self.task:
            self.fill_form_data()
    
    def fill_form_data(self):
        """用现有任务数据填充表单"""
        # 标题和描述
        self.title_input.setText(self.task["title"])
        self.desc_input.setText(self.task["description"])
        
        # 类别和优先级
        self.category_input.setCurrentText(self.task["category"])
        self.priority_input.setCurrentText(self.task["priority"])
        
        # 日期和时间
        due_date = QDate.fromString(self.task["due_date"], "yyyy-MM-dd")
        self.due_date_input.setDate(due_date)
        
        if self.task.get("start_time"):
            start_time = QTime.fromString(self.task["start_time"], "HH:mm")
            self.start_time_input.setTime(start_time)
        
        if self.task.get("end_time"):
            end_time = QTime.fromString(self.task["end_time"], "HH:mm")
            self.end_time_input.setTime(end_time)
        
        # 重复规则
        repeat_value = self.task.get("repeat", "不重复")
        self.repeat_input.setCurrentText(repeat_value)
        
        # 提醒设置
        if self.task.get("reminder_time"):
            self.reminder_check.setChecked(True)
            self.reminder_time.setValue(int(self.task["reminder_time"]))
        else:
            self.reminder_check.setChecked(False)
    
    def get_task_data(self):
        """获取表单数据
        
        Returns:
            dict: 任务数据
        """
        reminder_time = None
        if self.reminder_check.isChecked():
            reminder_time = self.reminder_time.value()
        
        task_data = {
            "title": self.title_input.text(),
            "description": self.desc_input.toPlainText(),
            "category": self.category_input.currentText(),
            "priority": self.priority_input.currentText(),
            "due_date": self.due_date_input.date().toString("yyyy-MM-dd"),
            "start_time": self.start_time_input.time().toString("HH:mm"),
            "end_time": self.end_time_input.time().toString("HH:mm"),
            "repeat": self.repeat_input.currentText() if self.repeat_input.currentText() != "不重复" else None,
            "reminder_time": reminder_time
        }
        
        return task_data


class TaskTableWidget(QTableWidget):
    """自定义任务表格组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化表格界面"""
        # 设置列数和列标题
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(["任务", "类别", "优先级", "日期", "时间", "状态"])
        
        # 设置表格属性
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)  # 不可编辑
        self.setSelectionBehavior(QTableWidget.SelectRows)  # 选择整行
        self.setSelectionMode(QTableWidget.SingleSelection)  # 单选
        self.verticalHeader().setVisible(False)  # 隐藏行号
        
        # 设置列宽
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
    
    def update_tasks(self, tasks):
        """
        更新任务列表
        
        Args:
            tasks: 任务列表
        """
        self.setRowCount(0)  # 清空表格
        
        for task in tasks:
            row_position = self.rowCount()
            self.insertRow(row_position)
            
            # 设置单元格内容
            self.setItem(row_position, 0, QTableWidgetItem(task["title"]))
            self.setItem(row_position, 1, QTableWidgetItem(task["category"]))
            self.setItem(row_position, 2, QTableWidgetItem(task["priority"]))
            self.setItem(row_position, 3, QTableWidgetItem(task["due_date"]))
            
            time_str = ""
            if task.get("start_time"):
                time_str = f"{task['start_time']}"
                if task.get("end_time"):
                    time_str += f" - {task['end_time']}"
            
            self.setItem(row_position, 4, QTableWidgetItem(time_str))
            
            status_text = "已完成" if task["completed"] else "未完成"
            status_item = QTableWidgetItem(status_text)
            
            # 根据状态设置颜色
            if task["completed"]:
                status_item.setForeground(QColor("green"))
            else:
                # 根据优先级设置未完成任务颜色
                if task["priority"] == Schedule.HIGH:
                    status_item.setForeground(QColor("red"))
                elif task["priority"] == Schedule.MEDIUM:
                    status_item.setForeground(QColor("orange"))
                else:
                    status_item.setForeground(QColor("blue"))
            
            self.setItem(row_position, 5, status_item)
            
            # 保存任务ID作为单元格的数据
            for col in range(6):
                item = self.item(row_position, col)
                item.setData(Qt.UserRole, task["id"])  # 保存任务ID


class CalendarViewWidget(QWidget):
    """月历视图组件"""
    
    def __init__(self, parent=None, schedule_manager=None,main_window=None):
        super().__init__(parent)
        self.schedule_manager = schedule_manager
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_layout = QHBoxLayout()
        self.month_title = QLabel("日历视图")
        self.month_title.setAlignment(Qt.AlignCenter)
        font = QFont("Roboto", 14)
        font.setBold(True)
        self.month_title.setFont(font)
        
        # 添加月份导航按钮
        self.prev_month_btn = QPushButton("上个月")
        self.prev_month_btn.clicked.connect(self.show_prev_month)
        
        self.next_month_btn = QPushButton("下个月")
        self.next_month_btn.clicked.connect(self.show_next_month)
        
        title_layout.addWidget(self.prev_month_btn)
        title_layout.addWidget(self.month_title)
        title_layout.addWidget(self.next_month_btn)
        
        main_layout.addLayout(title_layout)
        
        # 日历控件 - 使用自定义日历控件
        self.calendar = CustomCalendarWidget(schedule_manager=self.schedule_manager)
        self.calendar.setMinimumHeight(400)
        self.calendar.selectionChanged.connect(self.on_date_selected)
        self.update_month_title()
        
        # 监听月份变化
        self.calendar.currentPageChanged.connect(self.on_month_changed)
        
        # 当日任务列表
        self.task_label = QLabel("任务清单")
        self.task_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.task_label.setFont(font)
        
        self.task_table = TaskTableWidget()
        self.task_table.itemDoubleClicked.connect(self.edit_task)
        
        # 添加到布局
        main_layout.addWidget(self.calendar)
        main_layout.addWidget(self.task_label)
        main_layout.addWidget(self.task_table)
        
        self.setLayout(main_layout)
        
        # 初始化显示当天任务
        self.update_day_tasks()
        
        # 更新日历上的任务标记
        self.calendar.update_dates_with_tasks()

    def edit_task(self, item):
        """编辑任务"""
        # 获取任务ID
        task_id = item.data(Qt.UserRole)
        if not task_id:
            return
            
        task = self.schedule_manager.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "无法找到该任务")
            return
        
        # 打开编辑对话框
        dialog = TaskDialog(self, task)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            # 更新任务
            self.schedule_manager.update_task(task_id, **task_data)
            
            self.main_window.update_all_views()  # 通知主窗口更新所有视图


    def update_month_title(self):
        """更新月份标题"""
        current_month = self.calendar.monthShown()
        current_year = self.calendar.yearShown()
        month_names = ["一月", "二月", "三月", "四月", "五月", "六月", 
                       "七月", "八月", "九月", "十月", "十一月", "十二月"]
        self.month_title.setText(f"{current_year}年 {month_names[current_month-1]}")
    
    def on_month_changed(self, year, month):
        """月份变化时更新高亮任务日期"""
        self.update_month_title()
        self.calendar.update_dates_with_tasks()
    
    def show_prev_month(self):
        """显示上个月"""
        self.calendar.showPreviousMonth()
    
    def show_next_month(self):
        """显示下个月"""
        self.calendar.showNextMonth()
    
    def on_date_selected(self):
        """当选择日期改变时触发"""
        self.update_day_tasks()
    
    def update_day_tasks(self):
        """更新所选日期的任务列表"""
        if not self.schedule_manager:
            return
        
        # 获取所选日期
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        
        # 获取这一天的任务
        tasks = self.schedule_manager.get_tasks(from_date=selected_date, to_date=selected_date)
        
        # 更新标签
        self.task_label.setText(f"{selected_date} 任务清单 ({len(tasks)})")
        
        # 更新任务表
        self.task_table.update_tasks(tasks)

class WeekViewWidget(QWidget):
    """周视图组件 - 改进版，去掉时间段，只显示每天的任务"""
    
    def __init__(self, parent=None, schedule_manager=None,main_window=None):
        super().__init__(parent)
        self.schedule_manager = schedule_manager
        # 修正周起始日计算，确保从周一开始，并且时间部分为零
        now = datetime.now()
        # 修正：确保周一是起始日 (0=周一，6=周日)，并将时间部分设为零
        self.current_week_start = datetime(
            now.year, now.month, now.day, 0, 0, 0
        ) - timedelta(days=now.weekday())
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        
        # 添加导航控件
        nav_layout = QHBoxLayout()
        
        self.prev_week_btn = QPushButton("上一周")
        self.prev_week_btn.clicked.connect(self.show_prev_week)
        
        self.next_week_btn = QPushButton("下一周")
        self.next_week_btn.clicked.connect(self.show_next_week)
        
        self.current_week_label = QLabel()
        self.current_week_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.current_week_label.setFont(font)
        
        nav_layout.addWidget(self.prev_week_btn)
        nav_layout.addWidget(self.current_week_label)
        nav_layout.addWidget(self.next_week_btn)
        
        main_layout.addLayout(nav_layout)
        
        # 创建周视图表格 - 改为一周七天，每天只显示任务列表，不显示时间段
        self.week_grid = QGridLayout()
        self.week_grid.setSpacing(10)
        
        # 设置星期标题
        day_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day in enumerate(day_labels):
            label = QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #E3F2FD; border-radius: 4px;")
            self.week_grid.addWidget(label, 0, i)
        
        # 创建7个任务列表区域
        self.day_task_lists = []
        
        for i in range(7):
            # 创建日期标签
            date_label = QLabel()
            date_label.setAlignment(Qt.AlignCenter)
            date_label.setStyleSheet("padding: 3px; font-weight: bold;")
            self.week_grid.addWidget(date_label, 1, i)
            
            # 创建任务列表
            task_list = QTableWidget()
            task_list.setColumnCount(1)
            task_list.setHorizontalHeaderLabels(["任务"])
            
            # 设置表格属性
            task_list.setSelectionBehavior(QTableWidget.SelectRows)
            task_list.setEditTriggers(QTableWidget.NoEditTriggers)
            task_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            task_list.verticalHeader().setVisible(False)
            task_list.setStyleSheet("QTableWidget { border: 1px solid #E0E0E0; }")
            
            # 右键菜单
            task_list.setContextMenuPolicy(Qt.CustomContextMenu)
            task_list.customContextMenuRequested.connect(self.show_context_menu)
            
            # 添加双击编辑功能
            task_list.itemDoubleClicked.connect(self.edit_task)
            
            # 添加到网格布局
            self.week_grid.addWidget(task_list, 2, i)
            
            # 保存引用
            self.day_task_lists.append((date_label, task_list))
        
        self.week_grid.setRowStretch(2, 1)  # 让任务列表占用更多空间
        
        main_layout.addLayout(self.week_grid)
        
        # 任务详情区域
        task_detail_layout = QVBoxLayout()
        
        self.detail_label = QLabel("任务详情")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("font-weight: bold;")
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(100)
        
        task_detail_layout.addWidget(self.detail_label)
        task_detail_layout.addWidget(self.detail_text)
        
        main_layout.addLayout(task_detail_layout)
        
        self.setLayout(main_layout)
        
        # 更新当前视图
        self.update_week_view()
        
        # 连接点击事件
        for _, task_list in self.day_task_lists:
            task_list.itemClicked.connect(self.show_task_detail)

    def update_week_view(self):
        """更新周视图数据"""
        # 更新标题
        week_end = self.current_week_start + timedelta(days=6)
        self.current_week_label.setText(
            f"{self.current_week_start.strftime('%Y.%m.%d')} - {week_end.strftime('%Y.%m.%d')}"
        )
        
        # 获取本周任务
        start_date = self.current_week_start.strftime("%Y-%m-%d")
        end_date = week_end.strftime("%Y-%m-%d")
        
        tasks = self.schedule_manager.get_tasks(from_date=start_date, to_date=end_date)
        
        # 按日期分组任务
        daily_tasks = {i: [] for i in range(7)}
        
        for task in tasks:
            try:
                # 解析任务日期
                task_date = datetime.strptime(task["due_date"], "%Y-%m-%d")
                
                # 修正：使用日期对象计算差异，确保正确计算天数
                # 方法1：直接比较日期部分
                task_date_only = task_date.date()
                current_week_start_date_only = self.current_week_start.date()
                delta_days = (task_date_only - current_week_start_date_only).days
                
                if 0 <= delta_days < 7:
                    daily_tasks[delta_days].append(task)
            except Exception as e:
                logging.error(f"在周视图中处理任务时出错: {e}")
        
        # 更新每天的任务列表
        for day, (date_label, task_list) in enumerate(self.day_task_lists):
            # 设置日期标签 - 确保显示正确的日期
            day_date = self.current_week_start + timedelta(days=day)
            date_label.setText(day_date.strftime("%m-%d"))
            
            # 清空并更新任务列表
            task_list.setRowCount(0)
            day_tasks = daily_tasks[day]
            
            for task in day_tasks:
                row = task_list.rowCount()
                task_list.insertRow(row)
                
                # 设置任务标题
                title_item = QTableWidgetItem(task["title"])
                
                # 根据优先级和完成状态设置颜色
                if task["completed"]:
                    title_item.setForeground(QColor("green"))
                else:
                    if task["priority"] == Schedule.HIGH:
                        title_item.setForeground(QColor("red"))
                    elif task["priority"] == Schedule.MEDIUM:
                        title_item.setForeground(QColor("orange"))
                    else:
                        title_item.setForeground(QColor("blue"))
                
                # 添加任务时间作为提示
                if task.get("start_time"):
                    time_info = task["start_time"]
                    if task.get("end_time"):
                        time_info += f" - {task['end_time']}"
                    title_item.setToolTip(f"{time_info}\n{task.get('description', '')}")
                
                # 保存任务ID作为数据
                title_item.setData(Qt.UserRole, task["id"])
                
                task_list.setItem(row, 0, title_item)
            
            # 调整行高
            for row in range(task_list.rowCount()):
                task_list.setRowHeight(row, 25)
        
        # 强制刷新界面
        self.repaint()
        
    def edit_task(self, item):
        """编辑任务"""
        # 获取任务ID
        task_id = item.data(Qt.UserRole)
        if not task_id:
            return
            
        task = self.schedule_manager.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "无法找到该任务")
            return
        
        # 打开编辑对话框
        dialog = TaskDialog(self, task)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            # 更新任务
            self.schedule_manager.update_task(task_id, **task_data)
            
            self.main_window.update_all_views()  # 通知主窗口更新所有视图

    def show_prev_week(self):
        """显示上一周"""
        self.current_week_start -= timedelta(days=7)
        self.update_week_view()
    
    def show_next_week(self):
        """显示下一周"""
        self.current_week_start += timedelta(days=7)
        self.update_week_view()
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        # 获取触发事件的表格和项目
        sender = self.sender()
        item = sender.itemAt(position)
        
        if not item or not item.text():
            return
            
        # 获取任务ID
        task_id = item.data(Qt.UserRole)
        if not task_id:
            return
            
        task = self.schedule_manager.get_task(task_id)
        if not task:
            return
        
        # 创建右键菜单
        context_menu = QMenu(self)
        
        view_action = context_menu.addAction("查看任务详情")
        mark_action = context_menu.addAction("标记为" + ("未完成" if task["completed"] else "已完成"))
        
        # 执行菜单并获取选择的操作
        action = context_menu.exec_(sender.mapToGlobal(position))
        
        # 处理选择的操作
        if action == view_action:
            # 显示任务详情
            self.show_task_details(task)
        elif action == mark_action:
            # 切换完成状态
            self.schedule_manager.mark_completed(task_id, not task["completed"])
            self.update_week_view()
    
    def show_task_detail(self, item):
        """在下方详情区域显示任务详细信息"""
        task_id = item.data(Qt.UserRole)
        if not task_id:
            return
            
        task = self.schedule_manager.get_task(task_id)
        if not task:
            return
            
        # 显示任务详情
        details = (
            f"<b>任务:</b> {task['title']}<br>"
            f"<b>日期:</b> {task['due_date']}<br>"
            f"<b>时间:</b> {task.get('start_time', '无')} - {task.get('end_time', '无')}<br>"
            f"<b>类别:</b> {task['category']}<br>"
            f"<b>优先级:</b> {task['priority']}<br>"
            f"<b>状态:</b> {'已完成' if task['completed'] else '未完成'}<br>"
            f"<b>描述:</b> {task.get('description', '无')}"
        )
        
        self.detail_text.setHtml(details)
    
    def show_task_details(self, task):
        """弹窗显示任务详情"""
        msg = QMessageBox(self)
        msg.setWindowTitle("任务详情")
        
        details = (
            f"<b>任务:</b> {task['title']}<br>"
            f"<b>日期:</b> {task['due_date']}<br>"
            f"<b>时间:</b> {task.get('start_time', '无')} - {task.get('end_time', '无')}<br>"
            f"<b>类别:</b> {task['category']}<br>"
            f"<b>优先级:</b> {task['priority']}<br>"
            f"<b>状态:</b> {'已完成' if task['completed'] else '未完成'}<br>"
            f"<b>描述:</b> {task.get('description', '无')}"
        )
        
        msg.setText(details)
        msg.exec_()

class DayViewWidget(QWidget):
    """日视图组件 - 左侧显示时间段，右侧显示当日任务列表"""
    
    def __init__(self, parent=None, schedule_manager=None,main_window=None):
        super().__init__(parent)
        self.schedule_manager = schedule_manager
        self.current_date = datetime.now()
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        
        # 添加导航控件
        nav_layout = QHBoxLayout()
        
        self.prev_day_btn = QPushButton("前一天")
        self.prev_day_btn.clicked.connect(self.show_prev_day)
        
        self.today_btn = QPushButton("今天")
        self.today_btn.clicked.connect(self.show_today)
        
        # 添加日期选择器
        self.date_selector = QDateEdit()
        self.date_selector.setCalendarPopup(True)  # 允许弹出日历选择
        self.date_selector.setDisplayFormat("yyyy年MM月dd日")  # 设置日期格式
        self.date_selector.setDate(QDate.currentDate())  # 设置初始日期为今天
        
        # 添加"跳转"按钮
        self.go_to_date_btn = QPushButton("跳转")
        self.go_to_date_btn.clicked.connect(self.on_go_to_date)
        
        self.next_day_btn = QPushButton("后一天")
        self.next_day_btn.clicked.connect(self.show_next_day)
        
        self.current_day_label = QLabel()
        self.current_day_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.current_day_label.setFont(font)
        
        # 将日期选择器和跳转按钮添加到水平布局
        date_selector_layout = QHBoxLayout()
        date_selector_layout.addWidget(QLabel("选择日期:"))
        date_selector_layout.addWidget(self.date_selector)
        date_selector_layout.addWidget(self.go_to_date_btn)
        
        # 添加到导航布局
        nav_layout.addWidget(self.prev_day_btn)
        nav_layout.addWidget(self.today_btn)
        nav_layout.addLayout(date_selector_layout)
        nav_layout.addWidget(self.current_day_label)
        nav_layout.addWidget(self.next_day_btn)
        
        main_layout.addLayout(nav_layout)
        
        # 创建左右分栏布局
        split_layout = QHBoxLayout()
        
        # 左侧时间段显示
        time_slots_frame = QFrame()
        time_slots_frame.setFrameShape(QFrame.StyledPanel)
        time_slots_frame.setMinimumWidth(300)
        time_slots_layout = QVBoxLayout(time_slots_frame)
        
        time_slots_label = QLabel("时间安排")
        time_slots_label.setAlignment(Qt.AlignCenter)
        time_slots_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        time_slots_layout.addWidget(time_slots_label)
        
        # 创建时间段表格
        self.time_slots_table = QTableWidget()
        self.time_slots_table.setColumnCount(2)  # 两列：时间段和任务
        self.time_slots_table.setHorizontalHeaderLabels(["时间", "任务"])
        
        # 设置24小时
        self.time_slots_table.setRowCount(24)
        for hour in range(24):
            # 添加时间标签
            time_item = QTableWidgetItem(f"{hour:02d}:00")
            time_item.setTextAlignment(Qt.AlignCenter)
            self.time_slots_table.setItem(hour, 0, time_item)
        
        # 设置表格属性
        self.time_slots_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 不可编辑
        self.time_slots_table.setSelectionBehavior(QTableWidget.SelectRows)  # 选择整行
        self.time_slots_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.time_slots_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.time_slots_table.setShowGrid(True)
        
        # 添加到左侧布局
        time_slots_layout.addWidget(self.time_slots_table)
        
        # 右侧任务列表
        tasks_frame = QFrame()
        tasks_frame.setFrameShape(QFrame.StyledPanel)
        tasks_layout = QVBoxLayout(tasks_frame)
        
        tasks_label = QLabel("当日任务")
        tasks_label.setAlignment(Qt.AlignCenter)
        tasks_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        tasks_layout.addWidget(tasks_label)
        
        # 任务列表
        self.task_table = TaskTableWidget()

        self.task_table.itemDoubleClicked.connect(self.edit_task)
        
        tasks_layout.addWidget(self.task_table)
        
        # 添加到分栏布局
        split_layout.addWidget(time_slots_frame)
        split_layout.addWidget(tasks_frame)
        
        main_layout.addLayout(split_layout)
        
        # 设置布局
        self.setLayout(main_layout)
        
        # 更新当前视图
        self.update_day_view()

    def edit_task(self, item):
        """编辑任务"""
        # 获取任务ID
        task_id = item.data(Qt.UserRole)
        if not task_id:
            return
            
        task = self.schedule_manager.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "无法找到该任务")
            return
        
        # 打开编辑对话框
        dialog = TaskDialog(self, task)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            # 更新任务
            self.schedule_manager.update_task(task_id, **task_data)
            
            self.main_window.update_all_views()  # 通知主窗口更新所有视图


    def on_go_to_date(self):
        """点击跳转按钮时前往选择的日期"""
        # 获取日期选择器中的日期
        selected_date = self.date_selector.date().toPython()
        
        # 更新当前日期并刷新视图
        self.current_date = selected_date
        self.update_day_view()
    
    def update_day_view(self):
        """更新日视图数据"""
        # 同步日期选择器和当前日期
        self.date_selector.setDate(QDate(self.current_date.year, self.current_date.month, self.current_date.day))
        
        # 更新标题
        weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday = self.current_date.weekday()
        weekday_name = weekday_names[weekday]
        
        self.current_day_label.setText(
            f"{self.current_date.strftime('%Y年%m月%d日')} {weekday_name}"
        )
        
        # 清空时间段表格中的任务单元格
        for hour in range(24):
            self.time_slots_table.setItem(hour, 1, QTableWidgetItem(""))
            # 设置背景色为白色（重置）
            for col in range(2):
                item = self.time_slots_table.item(hour, col)
                if item:
                    item.setBackground(QColor(255, 255, 255))
        
        # 获取当天任务
        date_str = self.current_date.strftime("%Y-%m-%d")
        tasks = self.schedule_manager.get_tasks(from_date=date_str, to_date=date_str)
        
        # 记录有任务的时间段
        time_slots_with_tasks = set()
        
        # 在update_day_view方法中替换以下代码：

        # 更新左侧时间段视图
        for task in tasks:
            if task.get("start_time") and task.get("end_time"):
                try:
                    # 解析开始时间和结束时间
                    start_hour = int(task["start_time"].split(":")[0])
                    end_hour = int(task["end_time"].split(":")[0])
                    
                    # 如果结束时间小于开始时间，可能是跨天任务，这里只显示到当天结束
                    if end_hour < start_hour:
                        end_hour = 23
                    
                    # 首先添加任务文本到开始时间
                    if 0 <= start_hour < 24:
                        # 记录这个时间段有任务
                        time_slots_with_tasks.add(start_hour)
                        
                        # 获取现有任务文本
                        current_item = self.time_slots_table.item(start_hour, 1)
                        current_text = current_item.text() if current_item and current_item.text() else ""
                        
                        # 拼接新任务
                        if current_text:
                            new_text = f"{current_text}\n{task['title']}"
                        else:
                            new_text = task['title']
                        
                        # 创建任务项
                        task_item = QTableWidgetItem(new_text)
                        
                        # 设置颜色
                        if task["completed"]:
                            task_item.setForeground(QColor("green"))
                        else:
                            if task["priority"] == Schedule.HIGH:
                                task_item.setForeground(QColor("red"))
                            elif task["priority"] == Schedule.MEDIUM:
                                task_item.setForeground(QColor("orange"))
                            else:
                                task_item.setForeground(QColor("blue"))
                        
                        # 保存任务ID
                        task_item.setData(Qt.UserRole, task["id"])
                        
                        self.time_slots_table.setItem(start_hour, 1, task_item)
                    
                    # 然后仅标记其余时间段的颜色（不添加文本）
                    for hour in range(start_hour + 1, end_hour + 1):
                        if 0 <= hour < 24:
                            # 记录这个时间段有任务
                            time_slots_with_tasks.add(hour)
                            
                except Exception as e:
                    logging.error(f"在日视图中显示任务时出错: {e}")
            # 处理只有开始时间没有结束时间的任务
            elif task.get("start_time"):
                try:
                    # 解析开始时间
                    start_hour = int(task["start_time"].split(":")[0])
                    
                    if 0 <= start_hour < 24:
                        # 记录这个时间段有任务
                        time_slots_with_tasks.add(start_hour)
                        
                        # 获取现有任务文本
                        current_item = self.time_slots_table.item(start_hour, 1)
                        current_text = current_item.text() if current_item and current_item.text() else ""
                        
                        # 拼接新任务
                        if current_text:
                            new_text = f"{current_text}\n{task['title']}"
                        else:
                            new_text = task['title']
                        
                        # 创建任务项
                        task_item = QTableWidgetItem(new_text)
                        
                        # 设置颜色
                        if task["completed"]:
                            task_item.setForeground(QColor("green"))
                        else:
                            if task["priority"] == Schedule.HIGH:
                                task_item.setForeground(QColor("red"))
                            elif task["priority"] == Schedule.MEDIUM:
                                task_item.setForeground(QColor("orange"))
                            else:
                                task_item.setForeground(QColor("blue"))
                        
                        # 保存任务ID
                        task_item.setData(Qt.UserRole, task["id"])
                        
                        self.time_slots_table.setItem(start_hour, 1, task_item)
                except Exception as e:
                    logging.error(f"在日视图中显示任务时出错: {e}")

        # 设置有任务的时间段的背景色为浅蓝色
        for hour in time_slots_with_tasks:
            for col in range(2):
                item = self.time_slots_table.item(hour, col)
                if item:
                    item.setBackground(QColor(217, 232, 252))  # 浅蓝色背景
        
        # 更新右侧任务列表
        self.task_table.update_tasks(tasks)
    
    def show_prev_day(self):
        """显示前一天"""
        self.current_date -= timedelta(days=1)
        self.update_day_view()
    
    def show_today(self):
        """显示今天"""
        self.current_date = datetime.now()
        self.update_day_view()
    
    def show_next_day(self):
        """显示后一天"""
        self.current_date += timedelta(days=1)
        self.update_day_view()

    def show_task_details(self, task):
        """弹窗显示任务详情"""
        msg = QMessageBox(self)
        msg.setWindowTitle("任务详情")
        
        details = (
            f"<b>任务:</b> {task['title']}<br>"
            f"<b>日期:</b> {task['due_date']}<br>"
            f"<b>时间:</b> {task.get('start_time', '无')} - {task.get('end_time', '无')}<br>"
            f"<b>类别:</b> {task['category']}<br>"
            f"<b>优先级:</b> {task['priority']}<br>"
            f"<b>状态:</b> {'已完成' if task['completed'] else '未完成'}<br>"
            f"<b>描述:</b> {task.get('description', '无')}"
        )
        
        msg.setText(details)
        msg.exec_()



class ExcelExporter:
    """Excel导出工具类"""
    
    @staticmethod
    def export_tasks(tasks, filename):
        """
        将任务导出为Excel文件
        
        Args:
            tasks: 任务列表
            filename: 导出的文件名
            
        Returns:
            bool: 是否成功导出
        """
        try:
            # 创建DataFrame
            data = []
            for task in tasks:
                time_str = ""
                if task.get("start_time"):
                    time_str = task["start_time"]
                    if task.get("end_time"):
                        time_str += f" - {task['end_time']}"
                
                status = "已完成" if task["completed"] else "未完成"
                
                task_data = {
                    "任务": task["title"],
                    "描述": task.get("description", ""),
                    "类别": task["category"],
                    "优先级": task["priority"],
                    "日期": task["due_date"],
                    "时间": time_str,
                    "状态": status,
                    "创建时间": task.get("created_at", "")
                }
                data.append(task_data)
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 使用pandas直接导出到Excel
            df.to_excel(filename, sheet_name="任务列表", index=False)
            
            return True
            
        except Exception as e:
            logging.error(f"导出Excel时出错: {e}")
            return False


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 学号
        self.student_id_label = QLabel("学号:")
        self.student_id_input = QLineEdit()
        layout.addWidget(self.student_id_label)
        layout.addWidget(self.student_id_input)

        # 密码
        self.password_label = QLabel("密码:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)  # 隐藏密码输入
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # Chrome 地址
        self.chrome_path_label = QLabel("Chrome地址:")
        self.chrome_path_input = QLineEdit()
        layout.addWidget(self.chrome_path_label)
        layout.addWidget(self.chrome_path_input)

        # 按钮
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("取消")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # 连接信号
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)

        # 加载现有配置
        self.load_settings()

    def load_settings(self):
        """加载配置文件"""
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.student_id_input.setText(config.get("student_id", ""))
                self.password_input.setText(config.get("password", ""))
                self.chrome_path_input.setText(config.get("chrome_path", ""))

    def save_settings(self):
        """保存配置到文件"""
        config = {
            "student_id": self.student_id_input.text(),
            "password": self.password_input.text(),
            "chrome_path": self.chrome_path_input.text(),
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        self.accept()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, pet_state, pet, parent=None):
        super().__init__(parent)
        self.setObjectName("MainWindow")
        # 初始化宠物状态连接    
        self.pet_state = pet_state
        self.pet = pet
        self.init_pet_connection()

        # 初始化数据模型和提醒系统
        self.schedule_manager = Schedule()
        self.reminder = Reminder(self.schedule_manager)
        
        # 连接提醒信号
        self.reminder.reminder_signal.connect(self.show_reminder)
        
        # 初始化UI
        self.init_ui()
        
        # 启动提醒服务
        self.reminder.start()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle("日程管理与提醒工具")
        self.setMinimumSize(900, 650) # 窗口大小
        
        # 主布局容器
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        
        # 添加选项卡内容
        self.add_task_tab()
        self.add_calendar_tab()
        self.add_week_tab()
        self.add_day_tab()  # 新增日视图选项卡
        
        # 创建底部按钮栏
        button_layout = QHBoxLayout()

        self.add_task_btn = QPushButton("添加任务")
        self.add_task_btn.clicked.connect(self.add_task)

        self.export_btn = QPushButton("导出到Excel")
        self.export_btn.clicked.connect(self.export_to_excel)

        self.import_web_btn = QPushButton("从网页导入任务")
        self.import_web_btn.clicked.connect(self.import_from_web)

        self.settings_btn = QPushButton("设置")  # 新增“设置”按钮
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        # 添加到布局
        button_layout.addWidget(self.add_task_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.import_web_btn)
        button_layout.addWidget(self.settings_btn)  # 添加“设置”按钮
        button_layout.addStretch()

        # 添加到主布局
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(button_layout)

        # 状态栏
        self.statusBar().showMessage("日程管理与提醒工具已启动")
        
        # 显示窗口
        self.show()
    
    def open_settings_dialog(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            QMessageBox.information(self, "成功", "设置已保存")

    def add_task_tab(self):
        """添加任务列表选项卡"""
        task_tab = QWidget()
        task_layout = QVBoxLayout()
        
        # 过滤控件
        filter_layout = QHBoxLayout()
        
        # 创建过滤控件
        filter_layout.addWidget(QLabel("分类:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["全部", Schedule.WORK, Schedule.STUDY, Schedule.LIFE, Schedule.OTHER])
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addWidget(QLabel("优先级:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["全部", Schedule.HIGH, Schedule.MEDIUM, Schedule.LOW])
        filter_layout.addWidget(self.priority_filter)
        
        filter_layout.addWidget(QLabel("状态:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "未完成", "已完成"])
        filter_layout.addWidget(self.status_filter)
        
        self.apply_filter_btn = QPushButton("筛选")
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.apply_filter_btn)
        
        # 任务列表
        self.task_table = TaskTableWidget()
        self.task_table.itemDoubleClicked.connect(self.edit_task)
        
        # 右键菜单
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self.show_task_context_menu)
        
        # 将筛选控件和表格添加到布局
        task_layout.addLayout(filter_layout)
        task_layout.addWidget(self.task_table)
        
        task_tab.setLayout(task_layout)
        self.tabs.addTab(task_tab, "任务列表")
        
        # 初始加载所有任务
        self.update_task_list()
    
    def add_calendar_tab(self):
        """添加日历视图选项卡"""
        self.calendar_widget = CalendarViewWidget(schedule_manager=self.schedule_manager,main_window=self)
        self.tabs.addTab(self.calendar_widget, "月视图")
    
    def add_week_tab(self):
        """添加周视图选项卡"""
        self.week_widget = WeekViewWidget(schedule_manager=self.schedule_manager,main_window=self)
        self.tabs.addTab(self.week_widget, "周视图")
        
    def add_day_tab(self):
        """添加日视图选项卡"""
        self.day_widget = DayViewWidget(schedule_manager=self.schedule_manager,main_window=self)
        self.tabs.addTab(self.day_widget, "日视图")
    
    def update_task_list(self):
        """更新任务列表"""
        # 获取当前筛选条件
        category = None if self.category_filter.currentText() == "全部" else self.category_filter.currentText()
        priority = None if self.priority_filter.currentText() == "全部" else self.priority_filter.currentText()
        
        completed = None
        if self.status_filter.currentText() == "未完成":
            completed = False
        elif self.status_filter.currentText() == "已完成":
            completed = True
        
        # 获取符合条件的任务
        tasks = self.schedule_manager.get_tasks(category=category, priority=priority, completed=completed)
        
        # 更新表格
        self.task_table.update_tasks(tasks)
        
        # 更新状态栏
        self.statusBar().showMessage(f"当前显示 {len(tasks)} 个任务")
    
    def apply_filters(self):
        """筛选条件"""
        self.update_task_list()
    
    def add_task(self):
        """添加新任务"""
        dialog = TaskDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            # 添加任务
            task_id = self.schedule_manager.add_task(
                title=task_data["title"],
                description=task_data["description"],
                category=task_data["category"],
                priority=task_data["priority"],
                due_date=task_data["due_date"],
                start_time=task_data["start_time"],
                end_time=task_data["end_time"],
                repeat=task_data["repeat"],
                reminder_time=task_data["reminder_time"]
            )
            
            self.update_all_views()
            
            # 显示确认消息
            QMessageBox.information(self, "成功", f"已成功添加任务：{task_data['title']}")
    
    def edit_task(self, item):
        """编辑任务"""
        # 获取任务ID
        task_id = item.data(Qt.UserRole)
        task = self.schedule_manager.get_task(task_id)
        
        if not task:
            QMessageBox.warning(self, "错误", "无法找到该任务")
            return
        
        # 打开编辑对话框
        dialog = TaskDialog(self, task)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            # 更新任务
            self.schedule_manager.update_task(task_id, **task_data)
            
            # 更新界面
            self.update_all_views()
            
            # 显示确认消息
            QMessageBox.information(self, "成功", f"已成功更新任务：{task_data['title']}")
    
    def show_task_context_menu(self, position):
        """显示任务右键菜单"""
        item = self.task_table.itemAt(position)
        if not item:
            return
        
        # 获取任务ID
        task_id = item.data(Qt.UserRole)
        task = self.schedule_manager.get_task(task_id)
        
        if not task:
            return
        
        # 创建右键菜单
        context_menu = QMenu(self)
        
        edit_action = context_menu.addAction("编辑任务")
        delete_action = context_menu.addAction("删除任务")
        context_menu.addSeparator()
        
        if task["completed"]:
            complete_action = context_menu.addAction("标记为未完成")
        else:
            complete_action = context_menu.addAction("标记为已完成")
        
        context_menu.addSeparator()
        
        if task.get("reminder_time"):
            reminder_action = context_menu.addAction("移除提醒")
        else:
            reminder_action = context_menu.addAction("添加提醒")
        
        # 执行菜单并获取选择的操作
        action = context_menu.exec_(self.task_table.mapToGlobal(position))
        
        # 处理选择的操作
        if action == edit_action:
            self.edit_task(item)
        elif action == delete_action:
            self.delete_task(task_id)
        elif action == complete_action:
            self.toggle_task_complete(task_id)
        elif action == reminder_action:
            self.toggle_task_reminder(task_id)
    
    def delete_task(self, task_id):
        """删除任务"""
        task = self.schedule_manager.get_task(task_id)
        if not task:
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除任务 \"{task['title']}\" 吗？",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除任务
            self.schedule_manager.delete_task(task_id)

            self.update_all_views()
            
            # 显示确认消息
            QMessageBox.information(self, "成功", "任务已删除")
    
    def toggle_task_complete(self, task_id):
        """切换任务完成状态"""
        task = self.schedule_manager.get_task(task_id)
        if not task:
            return
        
        new_status = not task["completed"]
    
        # 更新任务状态
        if self.schedule_manager.mark_completed(task_id, new_status):
            # 更新宠物状态
            if new_status:
                # 完成任务奖励
                self.pet_state.hp = min(100, self.pet_state.hp + 10)
                self.pet_state.food = min(100, self.pet_state.food + 15)
                self.pet_state.mood = "happy"
            else:
                # 取消完成惩罚
                self.pet_state.hp = max(0, self.pet_state.hp - 5)
                self.pet_state.food = max(0, self.pet_state.food - 5)
                self.pet_state.mood = "angry"

        self.update_all_views()
    
    def toggle_task_reminder(self, task_id):
        """切换任务提醒状态"""
        task = self.schedule_manager.get_task(task_id)
        if not task:
            return
        
        if task.get("reminder_time"):
            # 移除提醒
            self.reminder.remove_reminder(task_id)
        else:
            # 添加提醒
            minutes_before, ok = QInputDialog.getInt(
                self, "设置提醒", 
                "提前多少分钟提醒？", 15, 1, 1440, 1
            )
            
            if ok:
                self.reminder.add_one_time_reminder(task_id, minutes_before)
        
        self.update_all_views()
    
    def show_reminder(self, task):
        """显示任务提醒"""
        title = "任务提醒"
        message = f"任务：{task['title']}\n时间：{task.get('start_time', '全天')}\n描述：{task['description']}"
        
        QMessageBox.information(self, title, message)
    
    def export_to_excel(self):
        """导出任务到Excel文件"""
        # 获取当前筛选条件下的任务
        category = None if self.category_filter.currentText() == "全部" else self.category_filter.currentText()
        priority = None if self.priority_filter.currentText() == "全部" else self.priority_filter.currentText()
        
        completed = None
        if self.status_filter.currentText() == "未完成":
            completed = False
        elif self.status_filter.currentText() == "已完成":
            completed = True
        
        # 获取符合条件的任务
        tasks = self.schedule_manager.get_tasks(category=category, priority=priority, completed=completed)
        
        if not tasks:
            QMessageBox.warning(self, "导出失败", "没有找到符合条件的任务")
            return
        
        # 打开文件保存对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出到Excel", 
            f"任务列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        
        if not filename:
            return  # 用户取消了保存
        
        # 导出到Excel
        if ExcelExporter.export_tasks(tasks, filename):
            QMessageBox.information(self, "导出成功", f"已成功导出 {len(tasks)} 个任务到 {filename}")
        else:
            QMessageBox.warning(self, "导出失败", "导出过程中发生错误")
    
    def closeEvent(self, event):
        """关闭窗口时的处理"""
        # 如果是用户点击关闭按钮，则只隐藏
        if QApplication.instance().closingDown():
            event.accept()
        else:
            self.hide()
            event.ignore()

    def update_all_views(self):
        """更新所有视图

        在任何视图中的任务变更后调用此方法，确保所有UI视图保持同步
        """
        try:
            # 更新任务列表
            self.update_task_list()
            
            # 更新日历视图
            if hasattr(self, 'calendar_widget'):
                self.calendar_widget.update_day_tasks()
                self.calendar_widget.calendar.update_dates_with_tasks()
            
            # 更新周视图
            if hasattr(self, 'week_widget'):
                self.week_widget.update_week_view()
            
            # 更新日视图
            if hasattr(self, 'day_widget'):
                self.day_widget.update_day_view()
            
            # 更新状态栏消息
            self.statusBar().showMessage("所有视图已更新")
        except Exception as e:
            logging.error(f"更新视图时出错: {e}")
            self.statusBar().showMessage(f"更新视图时出错: {e}")

    def init_pet_connection(self):
        # 连接状态变化信号
        self.pet_state.hp_changed.connect(self.update_pet_status)
        self.pet_state.mood_changed.connect(self.update_pet_animation)

    def update_pet_status(self, hp):
        if hp < 20:
            self.show_warning("宠物快饿死了！快去完成任务！")

    def update_pet_animation(self, mood):
        # 根据心情切换动画
        mood_animation_map = {
            "happy": "pet/happy.gif",
            "angry": "pet/angry.gif",
            "normal": "pet/default.gif"
        }
        self.pet.movie.setFileName(mood_animation_map[mood])
        self.pet.movie.start()
        self.pet.update()  # 强制刷新界面

    def import_from_web(self):
        """
        从网页导入任务
        """
        base_url= "教学网"
        self.schedule_manager.import_from_web(base_url)
        self.update_all_views()
        QMessageBox.information(self, "成功", "任务已从网页导入")
