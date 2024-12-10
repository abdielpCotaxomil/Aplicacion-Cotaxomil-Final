from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QDateTimeEdit, QMessageBox, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QDateTime
from openpyxl import Workbook
import os
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import psycopg2


class EditHistorialWindow(QMainWindow):
    def __init__(self, parent, db, folio):
        super(EditHistorialWindow, self).__init__(parent)
        self.parent = parent
        self.db = db
        self.folio = folio
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle('Editar Registro')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.eco_label = QLabel('Eco:')
        self.eco_combo = QComboBox(self)
        self.load_eco_options()
        layout.addWidget(self.eco_label)
        layout.addWidget(self.eco_combo)

        self.kilometraje_label = QLabel('Kilometraje:')
        self.kilometraje_edit = QLineEdit(self)
        layout.addWidget(self.kilometraje_label)
        layout.addWidget(self.kilometraje_edit)

        self.litros_diesel_label = QLabel('Litros Diesel:')
        self.litros_diesel_edit = QLineEdit(self)
        layout.addWidget(self.litros_diesel_label)
        layout.addWidget(self.litros_diesel_edit)

        self.save_button = QPushButton('Guardar Cambios', self)
        self.save_button.clicked.connect(self.save_changes)
        layout.addWidget(self.save_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def load_data(self):
        try:
            query = "SELECT eco, kilometraje, litros_diesel FROM historial_diesel WHERE folio = %s"
            self.db.cursor.execute(query, (self.folio,))
            result = self.db.cursor.fetchone()
            if result:
                eco = str(result[0])  # Convertir eco a cadena
                self.eco_combo.setCurrentText(eco)
                kilometraje = str(result[1])  # Convertir kilometraje a cadena
                self.kilometraje_edit.setText(kilometraje)
                litros_diesel = str(result[2])  # Convertir litros_diesel a cadena
                self.litros_diesel_edit.setText(litros_diesel)
            else:
                QMessageBox.warning(self, 'Advertencia', 'No se encontró el registro.', QMessageBox.Ok)
                self.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar datos: {e}', QMessageBox.Ok)

    def load_eco_options(self):
        try:
            query = "SELECT eco FROM autobus WHERE estatus = 'ACTIVO'"
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()
            self.eco_combo.addItem("Seleccionar Eco")
            for row in rows:
                eco_text = str(row[0])
                self.eco_combo.addItem(eco_text)
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar opciones de eco: {e}', QMessageBox.Ok)

    def save_changes(self):
        try:
            eco = self.eco_combo.currentText()
            kilometraje = self.kilometraje_edit.text()
            litros_diesel = float(self.litros_diesel_edit.text())

            if eco == "Seleccionar Eco" or not kilometraje or not litros_diesel :
                QMessageBox.warning(self, 'Advertencia', 'Por favor, complete todos los campos.', QMessageBox.Ok)
                return

            query_update = """
            UPDATE historial_diesel
            SET eco = %s, kilometraje = %s, litros_diesel = %s 
            WHERE folio = %s
            """
            self.db.cursor.execute(query_update, (eco, kilometraje, litros_diesel, self.folio))
            self.db.connection.commit()
            QMessageBox.information(self, 'Éxito', 'Registro actualizado correctamente.', QMessageBox.Ok)
            self.parent.load_historial_data()  # Actualizar la tabla en la ventana principal
            self.close()
        except psycopg2.Error as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al actualizar el registro: {e}', QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
