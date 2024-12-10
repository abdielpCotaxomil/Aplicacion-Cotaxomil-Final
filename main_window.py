from PyQt5.QtWidgets import QMainWindow, qApp, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from forms import AddBusForm, JornadaEntradaForm, JornadaSalidaForm, InfoForm
from database import Database

from admin_window import AdminWindow
from checadores_window import ChecadoresWindow
from recaudo_window import RecaudoWindow
from electromecanica_window import ElectromecanicaWindow
from diesel_window import DieselWindow
from golpes_window import GolpesWindow
from recursos_humanos_window import RecursosHumanosWindow
from siniestros_window import SiniestrosWindow  
from create_user import Create_User
from reloj_window import RelojWindow  # Asegúrate de importar la ventana para el botón "Vueltas"
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self, db_params, user_roles):
        super(MainWindow, self).__init__()
        self.db = Database(**db_params)
        self.user_roles = user_roles
        self.initUI()
        # Crear etiqueta de versión
        version_label = QLabel('Versión 1.3.2')
        version_label.setStyleSheet("padding: 5px;")

        # Añadir la etiqueta de versión a la barra de estado
        self.statusBar().addPermanentWidget(version_label)

        # Mantener referencias a las subventanas
        self.windows = {}

    def initUI(self):
        self.setWindowTitle('COTAXOMIL')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QHBoxLayout()

        # Menu Lateral
        menu_layout = QVBoxLayout()

        menu_label = QLabel("MENU")
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        menu_label.setFont(font)
        menu_layout.addWidget(menu_label, alignment=Qt.AlignCenter)

        # Botones del menú lateral
        self.adminButton = QPushButton('Administración', self)
        self.adminButton.setStyleSheet("padding: 10px;")
        self.adminButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.adminButton, alignment=Qt.AlignCenter)

        self.rhButton = QPushButton('Recursos Humanos', self)
        self.rhButton.setStyleSheet("padding: 10px;")
        self.rhButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.rhButton, alignment=Qt.AlignCenter)

        self.siniestrosButton = QPushButton('Siniestros', self)
        self.siniestrosButton.setStyleSheet("padding: 10px;")
        self.siniestrosButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.siniestrosButton, alignment=Qt.AlignCenter)

        self.checadorsButton = QPushButton('Checadores', self)
        self.checadorsButton.setStyleSheet("padding: 10px;")
        self.checadorsButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.checadorsButton, alignment=Qt.AlignCenter)

        self.recaudoButton = QPushButton('Recaudo', self)
        self.recaudoButton.setStyleSheet("padding: 10px;")
        self.recaudoButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.recaudoButton, alignment=Qt.AlignCenter)

        self.electroMecanicaButton = QPushButton('Electro-Mecánica', self)
        self.electroMecanicaButton.setStyleSheet("padding: 10px;")
        self.electroMecanicaButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.electroMecanicaButton, alignment=Qt.AlignCenter)

        self.dieselButton = QPushButton('Diesel', self)
        self.dieselButton.setStyleSheet("padding: 10px;")
        self.dieselButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.dieselButton, alignment=Qt.AlignCenter)

        self.golpesButton = QPushButton('Golpes', self)
        self.golpesButton.setStyleSheet("padding: 10px;")
        self.golpesButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.golpesButton, alignment=Qt.AlignCenter)

        self.vueltasButton = QPushButton('Relojes', self)  # Botón para "Vueltas"
        self.vueltasButton.setStyleSheet("padding: 10px;")
        self.vueltasButton.setStyleSheet("background-color: rgb(50,8,110);")
        menu_layout.addWidget(self.vueltasButton, alignment=Qt.AlignCenter)

        self.exitButton = QPushButton('Salir', self)
        self.exitButton.clicked.connect(qApp.quit)
        self.exitButton.setStyleSheet("padding: 10px;")
        self.exitButton.setStyleSheet("background-color: rgb(240, 20, 20);")
        menu_layout.addWidget(self.exitButton, alignment=Qt.AlignCenter)

        menu_layout.addStretch(1)  # Añadir espacio flexible para centrar el menú verticalmente

        # Placeholder para contenido principal
        image_label = QLabel(self)
        pixmap = QPixmap(resource_path("resources/cotaxomil.jpg"))
        scaled_pixmap = pixmap.scaled(pixmap.width() // 1, pixmap.height() // 1, Qt.KeepAspectRatio)
        image_label.setPixmap(scaled_pixmap)
        main_layout.addWidget(image_label)

        self.setLayout(main_layout)

        # Layout para el botón "Crear Usuario"
        bottom_left_layout = QVBoxLayout()
        bottom_left_layout.addStretch(1)  # Espacio flexible arriba del botón

        self.createUserButton = QPushButton('Crear Usuario', self)
        self.createUserButton.setStyleSheet("padding: 10px;")
        self.createUserButton.setStyleSheet("background-color: rgb(50,8,110);")
        bottom_left_layout.addWidget(self.createUserButton, alignment=Qt.AlignLeft)

        # Configuración de layouts principales
        main_layout.addLayout(menu_layout, 9)
        #main_layout.addLayout(content_layout, 4)
        main_layout.addLayout(bottom_left_layout)

        self.central_widget = QWidget()
        self.central_widget.setLayout(main_layout)
        self.setCentralWidget(self.central_widget)

        self.update_buttons_visibility()

        # Conectar botones a funciones
        self.adminButton.clicked.connect(self.show_admin_window)
        self.rhButton.clicked.connect(self.show_recursos_humanos_window)
        self.siniestrosButton.clicked.connect(self.show_siniestros_window)
        self.checadorsButton.clicked.connect(self.show_checadores_window)
        self.recaudoButton.clicked.connect(self.show_recaudo_window)
        self.electroMecanicaButton.clicked.connect(self.show_electromecanica_window)
        self.dieselButton.clicked.connect(self.show_diesel_window)
        self.golpesButton.clicked.connect(self.show_golpes_window)
        self.vueltasButton.clicked.connect(self.show_vueltas_window)  # Conectar el botón "Vueltas"
        self.createUserButton.clicked.connect(self.show_create_user)

    def update_buttons_visibility(self):
        # Verificar y mostrar u ocultar botones basados en roles
        self.adminButton.setVisible('administracion' in self.user_roles or 'system' in self.user_roles)
        self.rhButton.setVisible('administracion' in self.user_roles or 'system' in self.user_roles)
        self.siniestrosButton.setVisible('siniestros' in self.user_roles or 'system' in self.user_roles)
        self.checadorsButton.setVisible('checadores' in self.user_roles or 'system' in self.user_roles)
        self.recaudoButton.setVisible('recaudo' in self.user_roles or 'system' in self.user_roles)
        self.electroMecanicaButton.setVisible('electro_mecanica' in self.user_roles or 'system' in self.user_roles)
        self.dieselButton.setVisible('diesel' in self.user_roles or 'system' in self.user_roles)
        self.golpesButton.setVisible('golpes' in self.user_roles or 'system' in self.user_roles)
        self.vueltasButton.setVisible('tele' in self.user_roles or 'system' in self.user_roles)  # Mostrar botón "Vueltas"
        self.createUserButton.setVisible('system' in self.user_roles)  # Solo visible para 'system'

    def show_create_user(self):
        if 'system' in self.user_roles:
            self.create_user = Create_User(self.db)
            self.create_user.show()
        else:
            self.show_error_message()

    def show_admin_window(self):
        if 'administracion' in self.user_roles or 'system' in self.user_roles:
            if 'admin_window' not in self.windows:
                self.windows['admin_window'] = AdminWindow(self.db)
            self.windows['admin_window'].show()
        else:
            self.show_error_message()

    def show_recursos_humanos_window(self):
        if 'administracion' in self.user_roles or 'system' in self.user_roles:
            if 'rh_window' not in self.windows:
                self.windows['rh_window'] = RecursosHumanosWindow(self.db)
            self.windows['rh_window'].show()
        else:
            self.show_error_message()

    def show_siniestros_window(self):
        if 'siniestros' in self.user_roles or 'system' in self.user_roles:
            if 'siniestros_window' not in self.windows:
                self.windows['siniestros_window'] = SiniestrosWindow(self.db)
            self.windows['siniestros_window'].show()
        else:
            self.show_error_message()

    def show_checadores_window(self):
        if 'checadores' in self.user_roles or 'system' in self.user_roles:
            if 'checadors_window' not in self.windows:
                self.windows['checadors_window'] = ChecadoresWindow(self.db)
            self.windows['checadors_window'].show()
        else:
            self.show_error_message()

    def show_recaudo_window(self):
        if 'recaudo' in self.user_roles or 'system' in self.user_roles:
            if 'recaudo_window' not in self.windows:
                self.windows['recaudo_window'] = RecaudoWindow(self.db)
            self.windows['recaudo_window'].show()
        else:
            self.show_error_message()

    def show_electromecanica_window(self):
        if 'electro_mecanica' in self.user_roles or 'system' in self.user_roles:
            if 'electromecanica_window' not in self.windows:
                self.windows['electromecanica_window'] = ElectromecanicaWindow(self.db)
            self.windows['electromecanica_window'].show()
        else:
            self.show_error_message()

    def show_diesel_window(self):
        if 'diesel' in self.user_roles or 'system' in self.user_roles:
            if 'diesel_window' not in self.windows:
                self.windows['diesel_window'] = DieselWindow(self.db)
            self.windows['diesel_window'].show()
        else:
            self.show_error_message()

    def show_golpes_window(self):
        if 'golpes' in self.user_roles or 'system' in self.user_roles:
            if 'golpes_window' not in self.windows:
                self.windows['golpes_window'] = GolpesWindow(self.db)
            self.windows['golpes_window'].show()
        else:
            self.show_error_message()


    def show_vueltas_window(self):  # Método para mostrar la ventana "Vueltas"
        if 'tele' in self.user_roles or 'system' in self.user_roles:
            if 'reloj_window' not in self.windows:
                self.windows['reloj_window'] = RelojWindow(self.db)
            self.windows['reloj_window'].show()
        else:
            self.show_error_message()

    def show_error_message(self):
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("No tiene permiso para acceder a esta sección.")
        error_dialog.setIcon(QMessageBox.Warning)
        error_dialog.exec_()
