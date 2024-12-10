from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QFormLayout, QLineEdit, QMessageBox, QHBoxLayout, QLabel
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import Qt, QRegExp
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

class EditPatForm(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Lista de Empleados")
        self.setStyleSheet("font-size: 16px;")
        self.resize(600, 600)

        self.layout = QVBoxLayout()

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Buscar empleado...")
        self.search_bar.textChanged.connect(self.update_search_results)
        self.layout.addWidget(self.search_bar)
        
        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.list_widget)

        self.load_data_btn = QPushButton('Cargar Datos', self)
        self.load_data_btn.setStyleSheet("font-size: 16px;")
        self.load_data_btn.clicked.connect(self.load_data)
        self.layout.addWidget(self.load_data_btn)

        self.setLayout(self.layout)


    def load_data(self, search_text=""):
        try:
            if search_text:
                search_pattern = f"%{search_text}%"
                query = """
                SELECT num_empleado, nombre, apellido_paterno, apellido_materno
                FROM empleado_patio
                WHERE CAST(num_empleado AS TEXT) ILIKE %s OR
                      nombre ILIKE %s OR
                      apellido_paterno ILIKE %s OR
                      apellido_materno ILIKE %s
                ORDER BY num_empleado ASC
                """
                params = (search_pattern,) * 4
                self.db.cursor.execute(query, params)
            else:
                query = """
                SELECT num_empleado, nombre, apellido_paterno, apellido_materno
                FROM empleado_patio
                ORDER BY num_empleado ASC
                """
                self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()

            self.list_widget.clear()
            for row in rows:
                item_widget = QWidget()
                item_layout = QHBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)
                
                item_text = f"{row[0]} - {row[1]} {row[2]} {row[3]}"
                item_label = QLabel(item_text)
                item_label.setStyleSheet("font-size: 16px;")
                item_label.setFixedHeight(25)

                edit_btn = QPushButton("Editar")
                edit_btn.setStyleSheet("background-color: rgb(255, 165, 0); font-size: 16px;")
                edit_btn.setFixedSize(80, 50)
                edit_btn.clicked.connect(lambda ch, row=row: self.edit_item(row[0]))
                
                item_layout.addWidget(item_label)
                item_layout.addWidget(edit_btn)
                
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

    def edit_item(self, item_id):
        self.edit_window = EditWindow(self.db, item_id)
        self.edit_window.show()

class EditWindow(QWidget):
    def __init__(self, db, item_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.item_id = item_id
        self.setWindowTitle("Editar Empleado")
        self.setStyleSheet("font-size: 16px;")
        
        self.layout = QFormLayout()
        
        self.nombre = QLineEdit(self)
        self.nombre.setMaxLength(50)
        self.nombre.setPlaceholderText('Nombre')
        self.nombre.textChanged.connect(self.to_upper)
        self.layout.addRow('Nombre:', self.nombre)

        self.apellido_paterno = QLineEdit(self)
        self.apellido_paterno.setMaxLength(50)
        self.apellido_paterno.setPlaceholderText('Apellido Paterno')
        self.apellido_paterno.textChanged.connect(self.to_upper)
        self.layout.addRow('Apellido Paterno:', self.apellido_paterno)

        self.apellido_materno = QLineEdit(self)
        self.apellido_materno.setMaxLength(50)
        self.apellido_materno.setPlaceholderText('Apellido Materno')
        self.apellido_materno.textChanged.connect(self.to_upper)
        self.layout.addRow('Apellido Materno:', self.apellido_materno)

        self.puesto = QLineEdit(self)
        self.puesto.setMaxLength(50)
        self.puesto.setPlaceholderText('Puesto')
        self.puesto.textChanged.connect(self.to_upper)
        self.layout.addRow('Puesto:', self.puesto)

        self.salario = QLineEdit(self)
        self.salario.setMaxLength(12)
        self.salario.setPlaceholderText('99999999.99')
        self.salario.setValidator(QRegExpValidator(QRegExp(r'^\d{1,10}(\.\d{0,2})?$'), self))
        self.layout.addRow('Salario:', self.salario)

        self.rfc = QLineEdit(self)
        self.rfc.setMaxLength(13)
        self.rfc.setPlaceholderText('RFC')
        self.rfc.textChanged.connect(self.to_upper)
        self.layout.addRow('RFC:', self.rfc)

        self.nss = QLineEdit(self)
        self.nss.setMaxLength(11)
        self.nss.setPlaceholderText('NSS')
        self.nss.textChanged.connect(self.to_upper)
        self.layout.addRow('NSS:', self.nss)

        self.curp = QLineEdit(self)
        self.curp.setMaxLength(18)
        self.curp.setPlaceholderText('CURP')
        self.curp.textChanged.connect(self.to_upper)
        self.layout.addRow('CURP:', self.curp)

        self.update_btn = QPushButton('Actualizar Datos', self)
        self.update_btn.setStyleSheet("font-size: 16px;")
        self.update_btn.clicked.connect(self.update_data)
        self.layout.addWidget(self.update_btn)

        self.setLayout(self.layout)

        self.load_data()

    def to_upper(self):
        sender = self.sender()
        sender.setText(sender.text().upper())

    def load_data(self):
        try:
            query = """
            SELECT nombre, apellido_paterno, apellido_materno, puesto, salario, rfc, nss, curp
            FROM empleado_patio
            WHERE num_empleado = %s ORDER BY num_empleado ASC
            """
            self.db.cursor.execute(query, (self.item_id,))
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
                QMessageBox.warning(self, 'Error', 'No se encontró el chofer con el ID proporcionado', QMessageBox.Ok)
        except Exception as e:
            print(f"Error al cargar los datos: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar los datos: {e}', QMessageBox.Ok)

    def update_data(self):
        try:
            nombre = self.nombre.text()
            apellido_paterno = self.apellido_paterno.text()
            apellido_materno = self.apellido_materno.text()
            puesto = self.puesto.text()
            salario = self.salario.text()
            rfc = self.rfc.text()
            nss = self.nss.text()
            curp = self.curp.text()

            if not all([nombre, apellido_paterno, apellido_materno, puesto, salario, rfc, nss, curp]):
                QMessageBox.critical(self, 'Error', 'Todos los campos deben estar llenos', QMessageBox.Ok)
                return

            query = """
            UPDATE empleado_patio
            SET nombre = %s, apellido_paterno = %s, apellido_materno = %s, puesto = %s, salario = %s, rfc = %s, nss = %s, curp = %s
            WHERE num_empleado = %s
            """

            self.db.cursor.execute(query, (nombre, apellido_paterno, apellido_materno, puesto, salario, rfc, nss, curp, self.item_id))
            self.db.connection.commit()
            QMessageBox.information(self, 'Éxito', 'Datos actualizados correctamente', QMessageBox.Ok)
            self.close()
        except psycopg2.Error as e:
            self.db.connection.rollback()
            print(f"Error durante la actualización del query: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudo actualizar el chofer: {e}', QMessageBox.Ok)
        except Exception as e:
            print(f"Error inesperado: {e}")
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
