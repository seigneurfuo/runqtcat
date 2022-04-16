import configparser
import os
import time

import psutil
import sys
import pathlib
import configparser

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QDialog, QMenu, QSpinBox, QGridLayout, QLabel, QCheckBox, QLayout
from PyQt6.QtCore import QTimer, Qt, QSize

__author__ = "seigneurfuo"
__version__ = "2022.04.16"


class Application(QApplication):
    def __init__(self):
        super(QApplication, self).__init__(sys.argv)
        self.setQuitOnLastWindowClosed(False)

        # Variables & Co.
        self.config_parser = configparser.ConfigParser()
        self.settings = None
        self.config_filepath = None

        self.icons = {}

        # TODO: Personalisable depuis les préférences
        self.normal_color = "white"
        self.hdd_read_color = "darkblue"
        self.hdd_write_color = "darkred"

        self.color = self.normal_color
        self.current_icon_index = 0
        self.icons_folderpath = os.path.join(os.path.dirname(__file__), "gnome-runcat/src/icons/cat/")

        self.cpu_percent = 0
        self.interval = 0
        self.last_read_count = 0
        self.last_write_count = 0

        # Fonctions lancées pour initialiser un peut tout
        self.prepare_icons_ressources()
        self.load_settings()
        self.init_ui()

        self.tray.setVisible(True)

        # QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def init_ui(self):
        # Load translation (if any)

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.icons[self.color][0])

        # Menu clic droit
        menu = QMenu()
        menu.addAction(QIcon.fromTheme("dialog-information-symbolic"), self.tr("v.") + " " + __version__)

        show_settings_action = menu.addAction(QIcon.fromTheme("preferences"), self.tr("Settings"))
        show_settings_action.triggered.connect(self.show_settings)

        exit_action = menu.addAction(QIcon.fromTheme("window-close"), self.tr("Close"))
        exit_action.triggered.connect(self.close)  # FIXME: Trouver une meilleur façon de terminer l'application

        self.tray.setContextMenu(menu)

    def load_settings(self):
        self.config_filepath = os.path.join(pathlib.Path.home(), ".runqtcat.ini")
        self.defaut_settings = {
            "sleeping_threshold": 15,
            "animation_min_duration": 50,
            "animation_max_duration": 500,
            "hdd_activity_indicator": 0
        }

        if os.path.exists(self.config_filepath):
            self.config_parser.read(self.config_filepath)
            self.settings = self.config_parser["settings"]
        else:
            self.settings = self.defaut_settings

    def save_settings(self):
        self.config_parser["settings"] = self.settings
        with open(self.config_filepath, "w") as config_file:
            self.config_parser.write(config_file)

    def close(self):
        self.tray.setVisible(False)
        self.save_settings()
        exit(0)

    def prepare_icons_ressources(self):
        """Charge les icons et ajoute deux couleurs couleurs supplémentaires si on """
        icons = ["my-sleeping-symbolic.svg", "my-running-0-symbolic.svg", "my-running-1-symbolic.svg",
                 "my-running-2-symbolic.svg",
                 "my-running-3-symbolic.svg", "my-running-4-symbolic.svg"]

        for color in [self.normal_color, self.hdd_read_color, self.hdd_write_color]:  # TODO: Permetre de changer les couleurs dans les options
            for filename in icons:
                if color not in self.icons.keys():
                    self.icons[color] = []

                qpixmap = QPixmap(os.path.join(self.icons_folderpath, filename))
                colored_qpixmap = color_svg(qpixmap, color)
                colored_qicon = QIcon(colored_qpixmap)
                self.icons[color].append(colored_qicon)

    def show_settings(self):
        settings_window = SettingsWindow(self)
        settings_window.exec()
        settings_window.update_settings_from_gui()

        # Permet de remetre par défaut la couleur (corrige le bug si on désactive l'activité du disque, la couleur en cours reste sur l'icone)
        self.color = self.normal_color

    def tick(self):
        self.get_psutil_data()

        # Si activation de la led
        if self.settings["hdd_activity_indicator"] == "1" and (self.current_icon_index + 1) > int((self.cpu_percent / 25)):  # Permet d'éviter de faire flasher la couleur et attends un cicle en fonction du pourcenatge du cpu
            self.set_icon_color()

        self.set_icon_image()

        # Calcul de la vitesse
        self.timer.setInterval(self.interval)

    def get_psutil_data(self):
        self.cpu_percent = psutil.cpu_percent()
        # Inversion du pourcentage
        invert_cpu_percent = (100 - self.cpu_percent)
        percent_speed = (int(self.settings["animation_max_duration"]) - int(
            self.settings["animation_min_duration"])) / 100
        self.interval = int((percent_speed * invert_cpu_percent) + int(self.settings["animation_min_duration"]))

    def set_icon_color(self):
        # TODO: Changer le disque sur lequel on regader les mises à jours
        current_read_count = int(psutil.disk_io_counters()[0])
        current_write_count = int(psutil.disk_io_counters()[1])

        # Threashold
        read = (current_read_count > self.last_read_count)
        write = (current_write_count > self.last_write_count)

        if read and self.color != self.hdd_read_color:
            self.last_read_count = current_read_count
            self.color = self.hdd_read_color

        elif write and self.color != self.hdd_write_color:
            self.last_write_count = current_write_count
            self.color = self.hdd_write_color

        elif self.color != self.normal_color:
            self.color = self.normal_color

    def set_icon_image(self):
        # Affichage de l'icone
        sleeping = self.cpu_percent < int(self.settings["sleeping_threshold"])
        if sleeping:
            self.tray.setIcon(self.icons[self.color][0])
        else:
            self.tray.setIcon(self.icons[self.color][self.current_icon_index])

            # Boucle d'animation
            if self.current_icon_index == len(self.icons[self.color]) - 1:
                self.current_icon_index = 1
            else:
                self.current_icon_index += 1

        # Affichage de la durée (tooltip)
        self.tray.setToolTip(f"CPU: {self.cpu_percent}%")


class SettingsWindow(QDialog):
    def __init__(self, parent):
        super(QDialog, self).__init__(None)
        self.parent = parent
        self.settings = self.parent.settings

        self.init_ui()
        self.init_events()

    def init_events(self):
        self.sleeping_threshold_spinbox.valueChanged.connect(self.update_settings_from_gui)
        self.animation_min_duration_spinbox.valueChanged.connect(self.update_settings_from_gui)
        self.animation_max_duration_spinbox.valueChanged.connect(self.update_settings_from_gui)
        self.hdd_activity_indicator_checkbox.clicked.connect(self.update_settings_from_gui)

    def init_ui(self):
        self.setWindowTitle(self.tr("Settings"))

        layout = QGridLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        layout.addWidget(QLabel(self.tr("Sleeping trigger if CPU usage is smaller than:")), 0, 0)
        self.sleeping_threshold_spinbox = QSpinBox()
        self.sleeping_threshold_spinbox.setMinimum(1)
        self.sleeping_threshold_spinbox.setMaximum(99)
        self.sleeping_threshold_spinbox.setValue(int(self.settings["sleeping_threshold"]))
        layout.addWidget(self.sleeping_threshold_spinbox, 0, 1)

        layout.addWidget(QLabel(self.tr("Minimal frame duration (ms):")), 1, 0)
        self.animation_min_duration_spinbox = QSpinBox()
        self.animation_min_duration_spinbox.setMinimum(10)
        self.animation_min_duration_spinbox.setMaximum(10000)
        self.animation_min_duration_spinbox.setValue(int(self.settings["animation_min_duration"]))
        layout.addWidget(self.animation_min_duration_spinbox, 1, 1)

        layout.addWidget(QLabel(self.tr("Maximal frame duration (ms):")), 2, 0)
        self.animation_max_duration_spinbox = QSpinBox()
        self.animation_max_duration_spinbox.setMinimum(10)
        self.animation_max_duration_spinbox.setMaximum(10000)
        self.animation_max_duration_spinbox.setValue(int(self.settings["animation_max_duration"]))
        layout.addWidget(self.animation_max_duration_spinbox, 2, 1)

        layout.addWidget(QLabel(self.tr("Enable hard drive activity color status:")), 3, 0)
        self.hdd_activity_indicator_checkbox = QCheckBox()
        self.hdd_activity_indicator_checkbox.setChecked(bool(int(self.settings["hdd_activity_indicator"])))
        layout.addWidget(self.hdd_activity_indicator_checkbox, 3, 1)

        # About section
        layout.addWidget(QLabel(self.tr("Program:")), 4, 0)
        layout.addWidget(QLabel(f"{__author__} <a href=\"https://github.com/seigneurfuo/RunQtCat\">github.com/seigneurfuo/RunQtCat</a>"), 4, 1)

        layout.addWidget(QLabel(self.tr("Original RunCat program:")), 6, 0)
        url2_label = QLabel("Kyomesuke <a href=\"https://kyome.io/runcat/index.html?lang=en\">kyome.io/runcat/index.html?lang=en</a>")
        layout.addWidget(url2_label, 6, 1)

        layout.addWidget(QLabel(self.tr("Cat icons:")), 7, 0)
        url3_label = QLabel("win0err <a href=\"https://github.com/win0err/gnome-runcat\">github.com/win0err/gnome-runcat</a>")

        layout.addWidget(url3_label, 7, 1)

        self.setLayout(layout)

    def update_settings_from_gui(self):
        self.settings["sleeping_threshold"] = str(self.sleeping_threshold_spinbox.value())
        self.settings["animation_min_duration"] = str(self.animation_min_duration_spinbox.value())
        self.settings["animation_max_duration"] = str(self.animation_max_duration_spinbox.value())
        self.settings["hdd_activity_indicator"] = str(int(self.hdd_activity_indicator_checkbox.isChecked()))


def color_svg(img, color):
    qp = QPainter(img)
    qp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    qp.fillRect(img.rect(), QColor(color))
    qp.end()
    return img


if __name__ == "__main__":
    app = Application()
    app.exec()
