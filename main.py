#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日程管理与提醒工具

功能：
- 日程管理（添加、删除、修改日程）clean
- 提醒功能（定时提醒、重复提醒）
- 任务分类（工作、学习、生活等）
- 优先级设置（高、中、低）
- 日历视图（显示每日/每周/每月的任务安排）
- 数据存储：JSON 文件
"""

#5.25:现在的问题是运行自动打开教学网网页。我希望的是在ui里点一个按钮之后才自动进行爬取，并自动导入到任务栏里，最好也不要弹出网页
#再增加一个“设置”按钮，记录自己的教学网用户名，昵称，chrome地址，并储存。未设置的情况下不能使用爬取。
#点击“爬取”按钮之后，再出现一个弹窗，输入课程名。
import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui_manager import MainWindow
from pet_engine import PetState, DesktopPet
from my_schedule import Schedule

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')),
        logging.StreamHandler()
    ]
)

def main():
    """程序主入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("日程管理与提醒工具")

    # 初始化宠物系统
    pet_state = PetState()
    schedule = Schedule(pet_state=pet_state)
    schedule.check_overdue_tasks()

    # 设置应用程序图标
    app.setWindowIcon(QIcon('icons/logo.png'))

    # 只创建一个pet实例
    pet = DesktopPet(pet_state)
    pet.show()

    # 把pet实例传给主窗口
    window = MainWindow(pet_state, pet)
    window.show()

    # 启动应用程序事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()