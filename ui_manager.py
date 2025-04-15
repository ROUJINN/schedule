#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QDateEdit, QTimeEdit, QTextEdit,
    QMessageBox, QTabWidget, QScrollArea, QCalendarWidget, QDialog,
    QGridLayout, QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QFrame, QApplication, QStyle, QMenu, QAction
)
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, pyqtSlot, QSize
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont

# 导入项目其他模块
from schedule import Schedule
from reminder import Reminder

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
        self.title_label = QLabel("标题:")
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
        self.setHorizontalHeaderLabels(["标题", "类别", "优先级", "日期", "时间", "状态"])
        
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
    """日历视图组件"""
    
    def __init__(self, parent=None, schedule_manager=None):
        super().__init__(parent)
        self.schedule_manager = schedule_manager
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout()
        
        # 日历控件
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setMinimumHeight(300)
        
        self.calendar.selectionChanged.connect(self.on_date_selected)
        
        # 当日任务列表
        self.task_label = QLabel("任务清单")
        self.task_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.task_label.setFont(font)
        
        self.task_table = TaskTableWidget()
        
        # 添加到布局
        main_layout.addWidget(self.calendar)
        main_layout.addWidget(self.task_label)
        main_layout.addWidget(self.task_table)
        
        self.setLayout(main_layout)
        
        # 初始化显示当天任务
        self.update_day_tasks()
    
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
    
    def highlight_dates_with_tasks(self):
        """高亮有任务的日期"""
        # 这个功能需要自定义日历控件来实现
        # 在此作为功能扩展点
        pass


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
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
        self.setMinimumSize(800, 600)
        
        # 主布局容器
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        
        # 添加选项卡内容
        self.add_task_tab()
        self.add_calendar_tab()
        
        # 创建底部按钮栏
        button_layout = QHBoxLayout()
        
        self.add_task_btn = QPushButton("添加任务")
        self.add_task_btn.clicked.connect(self.add_task)
        
        # 添加到布局
        button_layout.addWidget(self.add_task_btn)
        button_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(button_layout)
        
        # 状态栏
        self.statusBar().showMessage("日程管理与提醒工具已启动")
        
        # 显示窗口
        self.show()
    
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
        
        self.apply_filter_btn = QPushButton("应用过滤")
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
        self.calendar_widget = CalendarViewWidget(schedule_manager=self.schedule_manager)
        self.tabs.addTab(self.calendar_widget, "日历视图")
    
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
        """应用过滤条件"""
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
            
            # 更新界面
            self.update_task_list()
            if self.calendar_widget:
                self.calendar_widget.update_day_tasks()
            
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
            self.update_task_list()
            if self.calendar_widget:
                self.calendar_widget.update_day_tasks()
            
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
            
            # 更新界面
            self.update_task_list()
            if self.calendar_widget:
                self.calendar_widget.update_day_tasks()
            
            # 显示确认消息
            QMessageBox.information(self, "成功", "任务已删除")
    
    def toggle_task_complete(self, task_id):
        """切换任务完成状态"""
        task = self.schedule_manager.get_task(task_id)
        if not task:
            return
        
        # 切换完成状态
        self.schedule_manager.mark_completed(task_id, not task["completed"])
        
        # 更新界面
        self.update_task_list()
        if self.calendar_widget:
            self.calendar_widget.update_day_tasks()
    
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
        
        # 更新界面
        self.update_task_list()
    
    def show_reminder(self, task):
        """显示任务提醒"""
        title = "任务提醒"
        message = f"任务：{task['title']}\n时间：{task.get('start_time', '全天')}\n描述：{task['description']}"
        
        QMessageBox.information(self, title, message)
    
    def closeEvent(self, event):
        """关闭窗口时的处理"""
        # 停止提醒线程
        self.reminder.stop()
        event.accept()