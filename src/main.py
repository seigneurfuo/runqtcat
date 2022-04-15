import os

import psutil
import sys
import time

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QDialog, QWidget, QMenu
from PyQt6.QtCore import QTimer

__version__ = "2022.04.15"

class MyApp(QApplication):
    def __init__(self):
        super(QApplication, self).__init__(sys.argv)
        self.setQuitOnLastWindowClosed(False)

        # Icons
        icons_folderpath = "../gnome-runcat/src/icons/cat/"

        self.sleeping_icon = QIcon(os.path.join(icons_folderpath, "my-sleeping-symbolic.svg"))
        self.running_icons = [
            QIcon(os.path.join(icons_folderpath, "my-running-0-symbolic.svg")),
            QIcon(os.path.join(icons_folderpath, "my-running-1-symbolic.svg")),
            QIcon(os.path.join(icons_folderpath, "my-running-2-symbolic.svg")),
            QIcon(os.path.join(icons_folderpath, "my-running-3-symbolic.svg")),
            QIcon(os.path.join(icons_folderpath, "my-running-4-symbolic.svg")),
        ]

        # Variables
        self.current_icon_index = 0

        # Config
        self.settings = {
            "sleeping_threshold": 15,
            "animation_min_duration": 50,
            "animation_max_duration": 500
        }

        self.init_ui()
        self.load_config()
        self.tray.setVisible(True)

        # QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def init_ui(self):
        # Load translation (if any)

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.sleeping_icon)

        # Menu clic droit
        menu = QMenu()
        menu.addAction(self.tr("v.") + " " + __version__)

        exit_action = menu.addAction(QIcon.fromTheme("window-close"), self.tr("Close"))
        exit_action.triggered.connect(self.close) # FIXME: Trouver une meilleur façon de terminer l'application

        self.tray.setContextMenu(menu)

    def load_config(self):
        pass

    def close(self):
        self.tray.setVisible(False)
        exit(0)

    def tick(self):
        cpu_percent = psutil.cpu_percent()

        # Inversion du pourcentage
        invert_cpu_percent = (100 - cpu_percent)
        percent_speed = (self.settings["animation_max_duration"] - self.settings["animation_min_duration"]) / 100
        interval = (percent_speed * invert_cpu_percent) + self.settings["animation_min_duration"]

        # Affichage de l'icone
        sleeping = cpu_percent < self.settings["sleeping_threshold"]
        if(sleeping):
            self.tray.setIcon(self.sleeping_icon)
        else:

            self.tray.setIcon(self.running_icons[self.current_icon_index])

            # Boucle d'animation
            if self.current_icon_index == len(self.running_icons) - 1:
                self.current_icon_index = 1
            else:
                self.current_icon_index += 1

        # Affichage de la durée (tooltip)
        self.tray.setToolTip(f"CPU: {cpu_percent}%")

        # Calcul de la vitesse
        self.timer.setInterval(int(interval))


app = MyApp()
app.exec()