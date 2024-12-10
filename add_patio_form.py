from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, 
    QMessageBox
)
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
import psycopg2
from empleado_info_window import EmpleadoInfoWindow

class AddPatioForm(QWidget):
    def __init__(self, db, parent=None):
        super(AddPatioForm, self).__init__(parent)
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Empleado')
        self.resize(400, 400)

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.nombre = QLineEdit(self)
        self.nombre.setMaxLength(50)
        self.nombre.setPlaceholderText('Nombre')
        self.nombre.textChanged.connect(self.to_upper)
        form_layout.addRow('Nombre:', self.nombre)

        self.apellido_paterno = QLineEdit(self)
        self.apellido_paterno.setMaxLength(50)
        self.apellido_paterno.setPlaceholderText('Apellido Paterno')
        self.apellido_paterno.textChanged.connect(self.to_upper)
        form_layout.addRow('Apellido Paterno:', self.apellido_paterno)

        self.apellido_materno = QLineEdit(self)
        self.apellido_materno.setMaxLength(50)
        self.apellido_materno.setPlaceholderText('Apellido Materno')
        self.apellido_materno.textChanged.connect(self.to_upper)
        form_layout.addRow('Apellido Materno:', self.apellido_materno)

        self.puesto = QLineEdit(self)
        self.puesto.setMaxLength(50)
        self.puesto.setPlaceholderText('Puesto')
        self.puesto.textChanged.connect(self.to_upper)
        form_layout.addRow('Puesto:', self.puesto)

        self.salario_base = QLineEdit(self)
        self.salario_base.setMaxLength(12)  # Permitirá hasta 10 dígitos y 2 decimales
        self.salario_base.setPlaceholderText('99999999.99')
        self.salario_base.setValidator(QRegExpValidator(QRegExp(r'^\d{1,10}(\.\d{0,2})?$'), self))  # Regex para validación
        form_layout.addRow('Salario Base:', self.salario_base)

        self.rfc = QLineEdit(self)
        self.rfc.setMaxLength(13)  # Limitar a 13 caracteres
        self.rfc.setPlaceholderText('RFC')
        self.rfc.textChanged.connect(self.to_upper)
        form_layout.addRow('RFC:', self.rfc)

        self.nss = QLineEdit(self)
        self.nss.setMaxLength(11)  # Limitar a 11 caracteres
        self.nss.setPlaceholderText('NSS')
        self.nss.textChanged.connect(self.to_upper)
        form_layout.addRow('NSS:', self.nss)

        self.curp = QLineEdit(self)
        self.curp.setMaxLength(18)  # Limitar a 18 caracteres
        self.curp.setPlaceholderText('CURP')
        self.curp.textChanged.connect(self.to_upper)
        form_layout.addRow('CURP:', self.curp)

        self.submit_btn = QPushButton('Agregar Empleado', self)
        self.submit_btn.clicked.connect(self.submit_form)
        form_layout.addRow(self.submit_btn)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def to_upper(self):
        sender = self.sender()
        sender.setText(sender.text().upper())

    def submit_form(self):
        try:
            query_folio = "SELECT nextval('folio_seq_siete')"
            self.db.cursor.execute(query_folio)
            folio = self.db.cursor.fetchone()[0]

            nombre = self.nombre.text()
            apellido_paterno = self.apellido_paterno.text()
            apellido_materno = self.apellido_materno.text()
            puesto = self.puesto.text()
            salario = self.salario_base.text()
            rfc = self.rfc.text()
            nss = self.nss.text()
            curp = self.curp.text()

            if not all([nombre, apellido_paterno, apellido_materno, puesto, salario, rfc, nss, curp]):
                QMessageBox.critical(self, 'Error', 'Todos los campos deben estar llenos', QMessageBox.Ok)
                return

            query = """
            INSERT INTO empleado_patio (num_empleado, nombre, apellido_paterno, apellido_materno, puesto, salario, rfc, nss, curp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            try:
                self.db.cursor.execute(query, (folio, nombre, apellido_paterno, apellido_materno, puesto, salario, rfc, nss, curp))
                self.db.connection.commit()  # Confirmar la transacción

                QMessageBox.information(self, 'Éxito', f'Empleado agregado correctamente con ID: {folio}', QMessageBox.Ok)
                self.close()
            except psycopg2.Error as e:
                self.db.connection.rollback()  # Deshacer los cambios en caso de error en la base de datos
                QMessageBox.critical(self, 'Error', f'No se pudo agregar el empleado: {e}', QMessageBox.Ok)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado fuera del formulario: {e}', QMessageBox.Ok)
    
    def fetch_patio_data(self, num_empleado):
        try:
            query = """
            SELECT num_empleado, nombre, apellido_paterno, apellido_materno, puesto, salario, rfc, nss, curp
            FROM empleado_patio
            WHERE num_empleado = %s
            """
            self.db.cursor.execute(query, (num_empleado,))
            row = self.db.cursor.fetchone()

            empleado_data = {
                "num_empleado": row[0],
                "Nombre": row[1],
                "Apellido Paterno": row[2],
                "Apellido Materno": row[3],
                "puesto": row[4],
                "salario": row[5],
                "rfc": row[6],
                "nss": row[7],
                "curp": row[8]
            }
            return empleado_data
        except Exception as e:
            print(f"Error obteniendo los datos del empleado: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudo obtener los datos del empleado: {e}', QMessageBox.Ok)
            return {}

    def show_empleado_info(self, empleado_data):
        self.empleado_info_window = EmpleadoInfoWindow(empleado_data)
        self.empleado_info_window.exec_()
