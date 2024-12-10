from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QFormLayout, QLineEdit, QMessageBox, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QDate
import psycopg2
import sys

class DatabaseConnection:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="tu_db",
            user="tu_usuario",
            password="tu_contraseña",
            host="localhost"
        )
        self.cursor = self.connection.cursor()

class InfoPat(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Lista de Empleados de Patio")
        self.resize(600, 600)

        self.layout = QVBoxLayout()

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Buscar empleado...")
        self.search_bar.textChanged.connect(self.update_search_results)
        self.layout.addWidget(self.search_bar)
        
        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)

        self.load_data_btn = QPushButton('Cargar Datos', self)
        self.load_data_btn.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el botón
        self.load_data_btn.clicked.connect(self.load_data)
        self.layout.addWidget(self.load_data_btn)

        self.setLayout(self.layout)


    def load_data(self, search_text=""):
        try:
            if search_text:
                search_pattern = f"%{search_text}%"
                query = """
                SELECT e.num_empleado, e.nombre, e.apellido_paterno, e.apellido_materno, e.puesto
                FROM empleado_patio e
                WHERE CAST(e.num_empleado AS TEXT) ILIKE %s OR
                      e.nombre ILIKE %s OR
                      e.apellido_paterno ILIKE %s OR
                      e.apellido_materno ILIKE %s OR
                      e.puesto ILIKE %s
                ORDER BY e.num_empleado ASC
                """
                params = (search_pattern,) * 5
                self.db.cursor.execute(query, params)
            else:
                query = """
                SELECT e.num_empleado, e.nombre, e.apellido_paterno, e.apellido_materno, e.puesto
                FROM empleado_patio e ORDER BY e.num_empleado ASC
                """
                self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()

            self.list_widget.clear()
            for row in rows:
                item_widget = QWidget()
                item_layout = QHBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)
                
                item_text = f"{row[0]} - {row[1]} {row[2]} {row[3]} - {row[4]}"
                item_label = QLabel(item_text)
                item_label.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para la etiqueta
                item_label.setFixedHeight(25)

                view_btn = QPushButton("Ver")
                view_btn.setStyleSheet("background-color: rgb(74, 193, 87); font-size: 15px;")  # Tamaño de fuente para el botón
                view_btn.setFixedSize(80, 50)  # Ajustar tamaño del botón para el texto más grande
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

    def update_search_results(self, text):
        self.load_data(text)

    def view_item(self, row):
        self.view_window = ViewWindow(self.db, row[0], row[1], row[2], row[3], row[4])
        self.view_window.show()

class ViewWindow(QWidget):
    def __init__(self, db, num_empleado, nombre, apellido_paterno, apellido_materno, puesto, parent=None):
        super().__init__(parent)
        self.db = db
        self.num_empleado = num_empleado
        self.nombre_str = nombre
        self.apellido_paterno_str = apellido_paterno
        self.apellido_materno_str = apellido_materno
        self.puesto_str = puesto
        self.setWindowTitle("Ver Empleado de Patio")
        
        self.layout = QFormLayout()
        
        self.nombre = QLineEdit(self)
        self.nombre.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el campo
        self.nombre.setReadOnly(True)
        self.layout.addRow('Nombre:', self.nombre)

        self.apellido_paterno = QLineEdit(self)
        self.apellido_paterno.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el campo
        self.apellido_paterno.setReadOnly(True)
        self.layout.addRow('Apellido Paterno:', self.apellido_paterno)

        self.apellido_materno = QLineEdit(self)
        self.apellido_materno.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el campo
        self.apellido_materno.setReadOnly(True)
        self.layout.addRow('Apellido Materno:', self.apellido_materno)

        self.puesto = QLineEdit(self)
        self.puesto.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el campo
        self.puesto.setReadOnly(True)
        self.layout.addRow('Puesto:', self.puesto)

        self.rfc = QLineEdit(self)
        self.rfc.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el campo
        self.rfc.setReadOnly(True)
        self.layout.addRow('RFC:', self.rfc)

        self.nss = QLineEdit(self)
        self.nss.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el campo
        self.nss.setReadOnly(True)
        self.layout.addRow('NSS:', self.nss)

        self.curp = QLineEdit(self)
        self.curp.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el campo
        self.curp.setReadOnly(True)
        self.layout.addRow('CURP:', self.curp)

        self.salario = QLineEdit(self)
        self.salario.setStyleSheet("font-size: 16px;")  # Tamaño de fuente para el campo
        self.salario.setReadOnly(True)
        self.layout.addRow('Salario:', self.salario)

        self.setLayout(self.layout)

        self.load_data()

    def load_data(self):
        try:
            query = """
            SELECT e.nombre, e.apellido_paterno, e.apellido_materno, e.puesto, e.salario, e.rfc, e.nss, e.curp
            FROM empleado_patio e
            WHERE e.num_empleado = %s ORDER BY e.num_empleado ASC
            """
            self.db.cursor.execute(query, (self.num_empleado,))
            row = self.db.cursor.fetchone()

            if row:
                self.nombre.setText(row[0])
                self.apellido_paterno.setText(row[1])
                self.apellido_materno.setText(row[2])
                self.puesto.setText(row[3])
                self.salario.setText(str(row[4]))
                self.rfc.setText(row[5])
                self.nss.setText(row[6])
                self.curp.setText(row[7])
            else:
                QMessageBox.warning(self, 'Error', 'No se encontró el empleado con el ID proporcionado', QMessageBox.Ok)
        except Exception as e:
            print(f"Error al cargar los datos: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar los datos: {e}', QMessageBox.Ok)
