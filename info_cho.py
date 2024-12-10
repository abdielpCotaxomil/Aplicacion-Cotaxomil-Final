import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, 
    QFormLayout, QLineEdit, QDateEdit, QMessageBox, QHBoxLayout, QLabel, QDialog, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QDate, pyqtSignal
import psycopg2
import psycopg2.extras
import sys

class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()

class DatabaseConnection:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="tu_db",
            user="tu_usuario",
            password="tu_contraseña",
            host="localhost",
            cursor_factory=psycopg2.extras.DictCursor
        )
        self.cursor = self.connection.cursor()

class InfoCho(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Lista de Choferes")
        self.resize(600, 800)

        self.layout = QVBoxLayout()

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Buscar chofer...")
        self.search_bar.setStyleSheet("font-size: 16px;")
        self.search_bar.textChanged.connect(self.update_search_results)
        self.layout.addWidget(self.search_bar)
        
        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("font-size: 16px;")  # Ajustar el tamaño de la fuente
        self.layout.addWidget(self.list_widget)

        self.load_data_btn = QPushButton('Cargar Datos', self)
        self.load_data_btn.setStyleSheet("font-size: 16px; background-color: rgb(255, 165, 0);")  # Ajustar el tamaño de la fuente y color
        self.load_data_btn.clicked.connect(self.load_data)
        self.layout.addWidget(self.load_data_btn)

        self.setLayout(self.layout)

    def load_data(self, search_text=""):
        try:
            # Modificar el query para incluir el texto de búsqueda
            if search_text:
                search_pattern = f"%{search_text}%"
                query = """
                SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, a.apodo
                FROM empleado_chofer e
                LEFT JOIN apodos a ON e.id_chofer = a.id_chofer
                WHERE e.estatus = 'ACTIVO' AND(
                CAST(e.id_chofer AS TEXT) ILIKE %s OR e.nombre ILIKE %s OR e.apellido_paterno ILIKE %s OR e.apellido_materno ILIKE %s OR a.apodo ILIKE %s)
                ORDER BY e.id_chofer ASC
                """
                # Ajustamos los parámetros para incluir el nuevo placeholder
                params = (search_pattern,) * 5
                self.db.cursor.execute(query, params)
            else:
                query = """
                SELECT e.id_chofer, e.nombre, e.apellido_paterno, e.apellido_materno, a.apodo
                FROM empleado_chofer e
                LEFT JOIN apodos a ON e.id_chofer = a.id_chofer WHERE e.estatus = 'ACTIVO' ORDER BY e.id_chofer ASC
                """
                self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()

            self.list_widget.clear()
            for row in rows:
                item_widget = QWidget()
                item_layout = QHBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)
                
                item_text = f"{row['id_chofer']} - {row['nombre']} {row['apellido_paterno']} {row['apellido_materno']}"
                if row['apodo']:
                    item_text += f" - \"<span style='color:red;'>{row['apodo']}</span>\""
                
                item_label = QLabel(item_text)
                item_label.setFixedHeight(25)
                item_label.setStyleSheet("font-size: 16px;")  # Ajustar el tamaño de la fuente
                item_label.setTextFormat(Qt.RichText)  # Para que el QLabel interprete el HTML

                view_btn = QPushButton("Ver")
                view_btn.setStyleSheet("background-color: rgb(74, 193, 87); font-size: 15px;")
                view_btn.setFixedSize(50, 36)
                view_btn.clicked.connect(lambda ch, row=row: self.view_item(row))
                
                item_layout.addWidget(item_label)
                item_layout.addWidget(view_btn)
                
                item_widget.setLayout(item_layout)
                
                list_item = QListWidgetItem(self.list_widget)
                list_item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, item_widget)
                
        except Exception as e:
            print(f"Error al cargar los datos: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar los datos: {e}', QMessageBox.Ok)
    
    def update_search_results(self):
        search_text = self.search_bar.text()
        self.load_data(search_text)

    def view_item(self, row):
        self.view_window = ViewWindow(self.db, row['id_chofer'])
        self.view_window.show()

class ViewWindow(QDialog):
    def __init__(self, db, item_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.item_id = item_id
        self.setWindowTitle("Ver Chofer")
        self.resize(600, 650)
        
        self.layout = QFormLayout()
        
        self.nombre = QLineEdit(self)
        self.nombre.setReadOnly(True)
        self.nombre.setStyleSheet("font-size: 16px;")
        self.layout.addRow('Nombre:', self.nombre)

        self.apellido_paterno = QLineEdit(self)
        self.apellido_paterno.setReadOnly(True)
        self.apellido_paterno.setStyleSheet("font-size: 16px;")
        self.layout.addRow('Apellido Paterno:', self.apellido_paterno)

        self.apellido_materno = QLineEdit(self)
        self.apellido_materno.setReadOnly(True)
        self.apellido_materno.setStyleSheet("font-size: 16px;")
        self.layout.addRow('Apellido Materno:', self.apellido_materno)

        self.telefono = QLineEdit(self)
        self.telefono.setReadOnly(True)
        self.telefono.setStyleSheet("font-size: 16px;")
        self.layout.addRow('Teléfono:', self.telefono)

        self.rfc = QLineEdit(self)
        self.rfc.setReadOnly(True)
        self.rfc.setStyleSheet("font-size: 16px;")
        self.layout.addRow('RFC:', self.rfc)

        self.nss = QLineEdit(self)
        self.nss.setReadOnly(True)
        self.nss.setStyleSheet("font-size: 16px;")
        self.layout.addRow('NSS:', self.nss)

        self.curp = QLineEdit(self)
        self.curp.setReadOnly(True)
        self.curp.setStyleSheet("font-size: 16px;")
        self.layout.addRow('CURP:', self.curp)

        self.salario_base = QLineEdit(self)
        self.salario_base.setReadOnly(True)
        self.salario_base.setStyleSheet("font-size: 16px;")
        self.layout.addRow('Salario Base:', self.salario_base)

        self.tipo_jornada = QLineEdit(self)
        self.tipo_jornada.setReadOnly(True)
        self.tipo_jornada.setStyleSheet("font-size: 16px;")
        self.layout.addRow('Tipo de Jornada:', self.tipo_jornada)

        self.fecha_vencimiento_tarjeton = QDateEdit(self)
        self.fecha_vencimiento_tarjeton.setReadOnly(True)
        self.fecha_vencimiento_tarjeton.setCalendarPopup(True)
        self.layout.addRow('Fecha de Vencimiento del Tarjetón:', self.fecha_vencimiento_tarjeton)

        self.apodo = QLineEdit(self)
        self.apodo.setReadOnly(True)
        self.apodo.setStyleSheet("font-size: 16px;")
        self.layout.addRow('Apodo:', self.apodo)

        self.load_data()
        self.load_photos()

        accept_button = QPushButton('Cerrar', self)
        accept_button.clicked.connect(self.accept)
        self.layout.addWidget(accept_button)

        self.setLayout(self.layout)

    def load_data(self):
        try:
            query = """
            SELECT e.nombre, e.apellido_paterno, e.apellido_materno, e.rfc, e.nss, e.curp, e.salario_base, e.tipo_jornada, e.fecha_vencimiento_tarjeton, e.telefono, a.apodo
            FROM empleado_chofer e
            LEFT JOIN apodos a ON e.id_chofer = a.id_chofer
            WHERE e.id_chofer = %s
            """
            self.db.cursor.execute(query, (self.item_id,))
            row = self.db.cursor.fetchone()

            if row:
                self.nombre.setText(row['nombre'])
                self.apellido_paterno.setText(row['apellido_paterno'])
                self.apellido_materno.setText(row['apellido_materno'])
                self.telefono.setText(row['telefono'])
                self.rfc.setText(row['rfc'])
                self.nss.setText(row['nss'])
                self.curp.setText(row['curp'])
                self.salario_base.setText(str(row['salario_base']))
                self.tipo_jornada.setText(row['tipo_jornada'])
                self.fecha_vencimiento_tarjeton.setDate(QDate.fromString(str(row['fecha_vencimiento_tarjeton']), 'yyyy-MM-dd'))
                self.apodo.setText(row['apodo'] if row['apodo'] else "")
            else:
                QMessageBox.warning(self, 'Error', 'No se encontró el chofer con el ID proporcionado', QMessageBox.Ok)
        except Exception as e:
            print(f"Error al cargar los datos: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar los datos: {e}', QMessageBox.Ok)

    def load_photos(self):
        try:
            query = """
            SELECT foto_chofer, foto_tarjeton_frontal, foto_credencial_frontal
            FROM empleado_chofer
            WHERE id_chofer = %s
            """
            self.db.cursor.execute(query, (self.item_id,))
            row = self.db.cursor.fetchone()

            photo_keys = ['foto_chofer', 'foto_tarjeton_frontal', 'foto_credencial_frontal']
            photo_labels = {
                'foto_chofer': "Foto del Operador:",
                'foto_tarjeton_frontal': "Foto Tarjetón Frontal:",
                'foto_credencial_frontal': "Foto Credencial Frontal:"
            }

            for key, photo_data in zip(photo_keys, row):
                if photo_data:
                    label = ClickableLabel(self)
                    pixmap = QPixmap()
                    pixmap.loadFromData(photo_data)
                    label.full_pixmap = pixmap
                    label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
                    label.clicked.connect(self.show_full_image)
                    self.layout.addRow(QLabel(photo_labels[key]), label)
                else:
                    self.layout.addRow(QLabel(photo_labels[key]), QLabel("Sin foto"))
        except Exception as e:
            print(f"Error al cargar las fotos: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar las fotos: {e}', QMessageBox.Ok)

    def show_full_image(self):
        label = self.sender()
        if hasattr(label, 'full_pixmap'):
            pixmap = label.full_pixmap
            dialog = QDialog(self)
            dialog.setWindowTitle("Imagen")
            dialog.resize(800, 600)
            layout = QVBoxLayout(dialog)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)

            # Escalar la imagen al tamaño de la ventana, conservando la relación de aspecto
            scaled_pixmap = pixmap.scaled(dialog.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)

            scroll_area.setWidget(image_label)
            layout.addWidget(scroll_area)

            # Conectar la señal para redimensionar la imagen cuando cambie el tamaño de la ventana
            dialog.resizeEvent = lambda event: image_label.setPixmap(pixmap.scaled(dialog.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

            dialog.exec_()

