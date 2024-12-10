import datetime
import os
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMessageBox, QInputDialog
)
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QLabel, QDialogButtonBox, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread
from add_chofer_form import AddChoferForm
from add_patio_form import AddPatioForm
from add_autobus_form import AddAutobusForm
from edit_cho_form import EditChoForm
from edit_pat_form import EditPatForm
from edit_aut_form import EditAutForm
from del_cho_form import DelChoForm
from del_pat_form import DelPatForm
from del_aut_form import DelAutForm
from info_cho import InfoCho
from info_pat import InfoPat
from info_aut import InfoAut


class AdminWindow(QMainWindow):
    def __init__(self, db):
        super(AdminWindow, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Administración')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        h_layout1 = QHBoxLayout()

        self.add_chofer_button = QPushButton('Agregar Chofer', self)
        self.add_chofer_button.clicked.connect(self.show_add_chofer_form)
        h_layout1.addWidget(self.add_chofer_button)

        self.edit_data_button = QPushButton('Editar Datos', self)
        self.edit_data_button.clicked.connect(self.show_edit_cho_form)
        self.edit_data_button.setStyleSheet("background-color: rgb(255, 165, 0);")
        self.edit_data_button.setFixedSize(120, 40)
        h_layout1.addWidget(self.edit_data_button)

        self.del_data_button = QPushButton('Eliminar Datos', self)
        self.del_data_button.clicked.connect(self.show_del_cho_form)
        self.del_data_button.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.del_data_button.setFixedSize(120, 40)
        h_layout1.addWidget(self.del_data_button)

        layout.addLayout(h_layout1)

        h_layout2 = QHBoxLayout()

        self.add_patio_button = QPushButton('Agregar Patio', self)
        self.add_patio_button.clicked.connect(self.show_add_patio_form)
        h_layout2.addWidget(self.add_patio_button)

        self.edit_patio_button = QPushButton('Editar Datos', self)
        self.edit_patio_button.clicked.connect(self.show_edit_pat_form)
        self.edit_patio_button.setStyleSheet("background-color: rgb(255, 165, 0);")
        self.edit_patio_button.setFixedSize(120, 40)
        h_layout2.addWidget(self.edit_patio_button)

        self.del_patio_button = QPushButton('Eliminar Datos', self)
        self.del_patio_button.clicked.connect(self.show_del_pat_form)
        self.del_patio_button.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.del_patio_button.setFixedSize(120, 40)
        h_layout2.addWidget(self.del_patio_button)

        layout.addLayout(h_layout2)

        h_layout3 = QHBoxLayout()

        self.add_bus_button = QPushButton('Agregar Autobus', self)
        self.add_bus_button.clicked.connect(self.show_add_autobus_form)
        h_layout3.addWidget(self.add_bus_button)

        self.edit_bus_button = QPushButton('Editar Datos', self)
        self.edit_bus_button.clicked.connect(self.show_edit_aut_form)
        self.edit_bus_button.setStyleSheet("background-color: rgb(255, 165, 0);")
        self.edit_bus_button.setFixedSize(120, 40)
        h_layout3.addWidget(self.edit_bus_button)

        self.del_bus_button = QPushButton('Eliminar Datos', self)
        self.del_bus_button.clicked.connect(self.show_del_aut_form)
        self.del_bus_button.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.del_bus_button.setFixedSize(120, 40)
        h_layout3.addWidget(self.del_bus_button)

        layout.addLayout(h_layout3)

        self.view_info_button = QPushButton('Ver Información', self)
        self.view_info_button.clicked.connect(self.show_info_options)
        layout.addWidget(self.view_info_button)

        self.check_tarjeton_button = QPushButton('Verificar Validez de Tarjetones', self)
        self.check_tarjeton_button.clicked.connect(self.check_tarjeton_validity)
        layout.addWidget(self.check_tarjeton_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def show_add_chofer_form(self):
        self.add_chofer_form = AddChoferForm(self.db)
        self.add_chofer_form.show()

    def show_add_patio_form(self):
        self.add_patio_form = AddPatioForm(self.db)
        self.add_patio_form.show()

    def show_add_autobus_form(self):
        self.add_autobus_form = AddAutobusForm(self.db)
        self.add_autobus_form.show()

    def show_edit_cho_form(self):
        self.edit_cho_form = EditChoForm(self.db)
        self.edit_cho_form.show()

    def show_edit_pat_form(self):
        self.edit_pat_form = EditPatForm(self.db)
        self.edit_pat_form.show()

    def show_edit_aut_form(self):
        self.edit_aut_form = EditAutForm(self.db)
        self.edit_aut_form.show()

    def show_del_cho_form(self):
        self.del_cho_form = DelChoForm(self.db)
        self.del_cho_form.show()

    def show_del_pat_form(self):
        self.del_pat_form = DelPatForm(self.db)
        self.del_pat_form.show()

    def show_del_aut_form(self):
        self.del_aut_form = DelAutForm(self.db)
        self.del_aut_form.show()

    def show_info_options(self):
        info_type, ok = QInputDialog.getItem(self, "Ver Información", "Selecciona el tipo de información a ver:", ["Chofer", "Patio", "Autobus"], 0, False)
        if ok and info_type:
            if info_type == "Chofer":
                self.show_chofer_info()
            elif info_type == "Patio":
                self.show_pat_info()
            elif info_type == "Autobus":
                self.show_aut_info()

    def show_chofer_info(self):
        self.info_chofer_window = InfoCho(self.db)
        self.info_chofer_window.show()

    def show_pat_info(self):
        self.info_pat_window = InfoPat(self.db)
        self.info_pat_window.show()

    def show_aut_info(self):
        self.info_aut_window = InfoAut(self.db)
        self.info_aut_window.show()

    def check_tarjeton_validity(self):
        dialog = TarjetonValidityDialog(self.db, self)
        dialog.exec_()

class TarjetonValidityDialog(QDialog):
    def __init__(self, db, parent=None):
        super(TarjetonValidityDialog, self).__init__(parent)
        self.db = db
        self.setWindowTitle("Validez de Tarjetones")
        self.resize(600, 400)
        self.initUI()
        self.load_data()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        
        # Barra de búsqueda
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Buscar chofer o estatus...")
        self.search_bar.textChanged.connect(self.update_search_results)
        self.layout.addWidget(self.search_bar)
        
        # Área de scroll
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)
        
        # Botón de cierre
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.layout.addWidget(self.button_box)
        
        # Almacenar la lista completa de choferes
        self.full_info = []
        
    def load_data(self):
        # Obtener datos de la base de datos
        query = "SELECT id_chofer, nombre, apellido_paterno, apellido_materno, fecha_vencimiento_tarjeton FROM empleado_chofer ORDER BY id_chofer ASC"
        try:
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()
            if results:
                today = datetime.date.today()
                one_month_later = today + datetime.timedelta(days=30)
                self.full_info = []
                for result in results:
                    id_chofer, nombre, apellido_paterno, apellido_materno, fecha_vencimiento = result
                    if today > fecha_vencimiento:
                        status_text = "Inválido"
                        status_html = "<span style='font-size: 16px; color: red;'>Inválido</span>"
                    elif today <= fecha_vencimiento <= one_month_later:
                        status_text = "Pendiente"
                        status_html = "<span style='font-size: 16px; color: blue;'>Pendiente</span>"
                    else:
                        status_text = "Válido"
                        status_html = "<span style='font-size: 16px; color: green;'>Válido</span>"
                    
                    info = {
                        'id_chofer': id_chofer,
                        'nombre_completo': f"{nombre} {apellido_paterno} {apellido_materno}",
                        'fecha_vencimiento': fecha_vencimiento,
                        'status': status_html,
                        'status_text': status_text.lower(),  # Para facilitar la búsqueda
                    }
                    self.full_info.append(info)
                
                self.display_data(self.full_info)
            else:
                QMessageBox.information(self, "Validez de Tarjetones", "No se encontraron registros.", QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al verificar la validez de los tarjetones: {e}", QMessageBox.Ok)
    
    def display_data(self, data_list):
        # Limpiar contenido previo
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        # Agregar datos al layout
        for info in data_list:
            label_text = (f"ID: <span style='font-size: 16px;'>{info['id_chofer']}</span><br>"
                          f"Chofer: <span style='font-size: 16px;'>{info['nombre_completo']}</span><br>"
                          f"Fecha de vencimiento: <span style='font-size: 16px;'>{info['fecha_vencimiento']}</span> - Tarjetón: "
                          f"{info['status']}")
            label = QLabel(label_text)
            label.setTextFormat(Qt.RichText)
            label.setWordWrap(True)
            self.scroll_layout.addWidget(label)
    
    def update_search_results(self, text):
        # Filtrar self.full_info basado en el texto de búsqueda
        filtered_data = []
        search_text = text.lower()
        for info in self.full_info:
            if (search_text in str(info['id_chofer']).lower() or
                search_text in info['nombre_completo'].lower() or
                search_text in info['status_text']):
                filtered_data.append(info)
        self.display_data(filtered_data)
