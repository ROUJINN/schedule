#!/usr/bin/env python3

import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui_manager import MainWindow
from pet_engine import PetState, DesktopPet
from my_schedule import Schedule

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')),
        logging.StreamHandler()
    ]
)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("日程管理与提醒工具")

    pet_state = PetState()
    schedule = Schedule(pet_state=pet_state)
    schedule.check_overdue_tasks()

    app.setWindowIcon(QIcon('icons/logo.png'))

    pet = DesktopPet(pet_state)
    pet.show()

    window = MainWindow(pet_state, pet)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()