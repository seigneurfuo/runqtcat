import configparser
import os

import psutil
import sys
import pathlib
import configparser

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QDialog, QMenu, QSpinBox, QGridLayout, QLabel
from PyQt6.QtCore import QTimer, Qt

__version__ = "2022.04.15"


class MyApp(QApplication):
    def __init__(self):
        super(QApplication, self).__init__(sys.argv)
        self.setQuitOnLastWindowClosed(False)

        self.settings = configparser.ConfigParser()

        # Icons
        icons_folderpath = os.path.join(os.path.dirname(__file__), "gnome-runcat/src/icons/cat/")

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

        self.init_ui()
        self.load_settings()
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

        show_settings_action = menu.addAction(QIcon.fromTheme("document-properties"), self.tr("Settings"))
        show_settings_action.triggered.connect(self.show_settings)

        exit_action = menu.addAction(QIcon.fromTheme("window-close"), self.tr("Close"))
        exit_action.triggered.connect(self.close)  # FIXME: Trouver une meilleur façon de terminer l'application

        self.tray.setContextMenu(menu)

    def load_settings(self):
        # Config
        self.config_filepath = os.path.join(pathlib.Path.home(), ".runqtcat.ini")
        self.defaut_settings = {
            "sleeping_threshold": 15,
            "animation_min_duration": 50,
            "animation_max_duration": 500
        }

        if not os.path.exists(self.config_filepath):
            self.settings["settings"] = self.defaut_settings
        else:
            self.settings.read(self.config_filepath)

    def save_settings(self):
        with open(self.config_filepath, "w") as config_file:
            self.settings.write(config_file)

    def close(self):
        self.tray.setVisible(False)
        self.save_settings()
        exit(0)

    def show_settings(self):
        settings_window = SettingsWindow(self.settings)
        settings_window.exec()
        settings_window.get_settings()

    def tick(self):
        cpu_percent = psutil.cpu_percent()

        # Inversion du pourcentage
        invert_cpu_percent = (100 - cpu_percent)
        percent_speed = (int(self.settings["settings"]["animation_max_duration"]) - int(
            self.settings["settings"]["animation_min_duration"])) / 100
        interval = (percent_speed * invert_cpu_percent) + int(self.settings["settings"]["animation_min_duration"])

        # Affichage de l'icone
        sleeping = cpu_percent < int(self.settings["settings"]["sleeping_threshold"])
        if sleeping:
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


class SettingsWindow(QDialog):
    def __init__(self, settings):
        super(QDialog, self).__init__(None)
        self.setWindowTitle(self.tr("Settings"))
        self.settings = settings

        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        layout.addWidget(QLabel(self.tr("Sleeping threshold:")), 0, 0)
        self.sleeping_threshold_spinbox = QSpinBox()
        self.sleeping_threshold_spinbox.setMinimum(1)
        self.sleeping_threshold_spinbox.setMaximum(99)
        self.sleeping_threshold_spinbox.setValue(int(self.settings["settings"]["sleeping_threshold"]))
        layout.addWidget(self.sleeping_threshold_spinbox, 0, 1)

        layout.addWidget(QLabel(self.tr("Minimal frame duration (ms):")), 1, 0)
        self.animation_min_duration_spinbox = QSpinBox()
        self.animation_min_duration_spinbox.setMinimum(10)
        self.animation_min_duration_spinbox.setMaximum(10000)
        self.animation_min_duration_spinbox.setValue(int(self.settings["settings"]["animation_min_duration"]))
        layout.addWidget(self.animation_min_duration_spinbox, 1, 1)

        layout.addWidget(QLabel(self.tr("Maximal frame duration (ms):")), 2, 0)
        self.animation_max_duration_spinbox = QSpinBox()
        self.animation_max_duration_spinbox.setMinimum(10)
        self.animation_max_duration_spinbox.setMaximum(10000)
        self.animation_max_duration_spinbox.setValue(int(self.settings["settings"]["animation_max_duration"]))
        layout.addWidget(self.animation_max_duration_spinbox, 2, 1)

        # About section
        layout.addWidget(QLabel(self.tr("Program:") + "seigneufuo"), 4, 0)
        layout.addWidget(
            QLabel("<a href=\"https://github.com/seigneurfuo/RunQtCat\">github.com/seigneurfuo/RunQtCat</a>"), 4, 1)

        layout.addWidget(QLabel(self.tr("Original RunCat program:") + "Kyomesuke"), 6, 0)
        url2_label = QLabel(
            "<a href=\"https://kyome.io/runcat/index.html?lang=en\">kyome.io/runcat/index.html?lang=en</a>")
        layout.addWidget(url2_label, 6, 1)

        layout.addWidget(QLabel(self.tr("Cat icons:") + "win0err"), 7, 0)
        url3_label = QLabel("<a href=\"https://github.com/win0err/gnome-runcat\">github.com/win0err/gnome-runcat</a>")

        layout.addWidget(url3_label, 7, 1)

        self.setLayout(layout)

    def get_settings(self):
        self.settings["settings"]["sleeping_threshold"] = str(self.sleeping_threshold_spinbox.value())
        self.settings["settings"]["animation_min_duration"] = str(self.animation_min_duration_spinbox.value())
        self.settings["settings"]["animation_max_duration"] = str(self.animation_max_duration_spinbox.value())


app = MyApp()
app.exec()
