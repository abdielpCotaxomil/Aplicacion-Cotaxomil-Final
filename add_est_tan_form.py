from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QDateTimeEdit, QMessageBox, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import QDateTime, QRegExp
from PyQt5.QtGui import QRegExpValidator
from openpyxl import Workbook
import psycopg2
import os
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from edit_hist_win import EditHistorialWindow

class AddEstTanForm(QMainWindow):
    def __init__(self, db):
        super(AddEstTanForm, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Estado del tanque')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Generado automáticamente')
        layout.addWidget(self.folio_label)

        self.fecha_hora_label = QLabel('Fecha y Hora:')
        self.fecha_hora_edit = QDateTimeEdit(self)
        self.fecha_hora_edit.setDateTime(QDateTime.currentDateTime())
        self.fecha_hora_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        self.fecha_hora_edit.setReadOnly(True)
        layout.addWidget(self.fecha_hora_label)
        layout.addWidget(self.fecha_hora_edit)

        self.cuenta_litros_inicial_label = QLabel('Litros inicial:')
        self.cuenta_litros_inicial_edit = QLineEdit(self)
        self.cuenta_litros_inicial_edit.setMaxLength(12)
        self.cuenta_litros_inicial_edit.setPlaceholderText('99999999.99')
        self.cuenta_litros_inicial_edit.setValidator(QRegExpValidator(QRegExp(r'^\d{1,10}(\.\d{0,2})?$'), self))
        layout.addWidget(self.cuenta_litros_inicial_label)
        layout.addWidget(self.cuenta_litros_inicial_edit)

        self.add_recaudo_button = QPushButton('Mostrar Datos', self)
        self.add_recaudo_button.clicked.connect(self.show_saved_form)
        self.add_recaudo_button.setStyleSheet('background-color: rgb(88, 129, 216 );; color: white;')
        layout.addWidget(self.add_recaudo_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def show_saved_form(self):
        fecha_hora = self.fecha_hora_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss')
        cuenta_litros_inicial = self.cuenta_litros_inicial_edit.text()

        self.saved_form = RecSavedForm(self, self.db, fecha_hora, cuenta_litros_inicial)
        self.saved_form.show()
        self.close()

class RecSavedForm(QMainWindow):
    def __init__(self, parent, db, fecha_hora, cuenta_litros_inicial):
        super(RecSavedForm, self).__init__(parent)
        self.parent = parent
        self.db = db
        self.fecha_hora = fecha_hora
        self.cuenta_litros_inicial = cuenta_litros_inicial
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Estado del Tanque')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Será generado al guardar')
        layout.addWidget(self.folio_label)

        self.fecha_hora_label = QLabel(f'Fecha y Hora: {self.fecha_hora}')
        layout.addWidget(self.fecha_hora_label)

        self.litros_inicial_label = QLabel(f'Litros inicial: {self.cuenta_litros_inicial}')
        layout.addWidget(self.litros_inicial_label)

        buttons_layout = QHBoxLayout()

        self.accept_button = QPushButton('Aceptar', self)
        self.accept_button.clicked.connect(self.accept)
        self.accept_button.setStyleSheet("background-color: rgb(88, 129, 216 );")
        buttons_layout.addWidget(self.accept_button)

        self.edit_button = QPushButton('Editar', self)
        self.edit_button.clicked.connect(self.edit)
        self.edit_button.setStyleSheet("background-color: rgb(88, 129, 216 );")
        buttons_layout.addWidget(self.edit_button)

        layout.addLayout(buttons_layout)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def accept(self):
        try:
            fecha_actual = QDateTime.currentDateTime().toString('yyyy-MM-dd')

            # Verificar si ya existe un registro para la fecha actual
            query_check = "SELECT COUNT(*) FROM cuenta_litros WHERE fecha = %s"
            self.db.cursor.execute(query_check, (fecha_actual,))
            count = self.db.cursor.fetchone()[0]

            if count > 0:
                QMessageBox.information(self, 'Información', 'Ya existe un registro para la fecha actual. Redirigiendo al historial.', QMessageBox.Ok)
                self.open_historial_diesel_window()
                self.close()
                return

            # Generar folio automáticamente (entero)
            query_folio = "SELECT nextval('folio_seq_dos')"
            self.db.cursor.execute(query_folio)
            folio = self.db.cursor.fetchone()[0]

            # Extraer la hora sin microsegundos
            hora_formateada = QDateTime.fromString(self.fecha_hora, 'yyyy-MM-dd HH:mm:ss').toString('HH:mm:ss')

            query_insert = """
            INSERT INTO cuenta_litros (folio, fecha, hora, cuenta_litros_inicial)
            VALUES (%s, current_date, %s, %s)
            """
            self.db.cursor.execute(query_insert, (folio, hora_formateada, self.cuenta_litros_inicial))
            self.db.connection.commit()

            QMessageBox.information(self, 'Éxito', 'Recaudo agregado correctamente.', QMessageBox.Ok)
            self.open_historial_diesel_window()  # Abrir la ventana de historial de diesel
            self.close()

        except psycopg2.Error as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al agregar recaudo: {e}', QMessageBox.Ok)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)

    def edit(self):
        self.close()
        self.parent.show()

    def open_historial_diesel_window(self):
        self.historial_diesel_window = HistorialDieselWindow(self, self.db)
        self.historial_diesel_window.show()

class HistorialDieselWindow(QMainWindow):
    def __init__(self, parent, db):
        super(HistorialDieselWindow, self).__init__(parent)
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Historial de Diesel')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.historial_table = QTableWidget(self)
        self.historial_table.setColumnCount(6)  # Cambiado a 6 para incluir "Litros Final"
        self.historial_table.setHorizontalHeaderLabels(['Folio', 'Fecha', 'Hora', 'Eco', 'Kilometraje', 'Litros Diesel'])
        
        layout.addWidget(self.historial_table)

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
        self.litros_diesel_edit.setMaxLength(12)
        self.litros_diesel_edit.setPlaceholderText('99999999.99')
        self.litros_diesel_edit.setValidator(QRegExpValidator(QRegExp(r'^\d{1,10}(\.\d{0,2})?$'), self))
        layout.addWidget(self.litros_diesel_label)
        layout.addWidget(self.litros_diesel_edit)

        self.litros_final_label = QLabel('Litros Final:')
        self.litros_final_edit = QLineEdit(self)
        self.litros_final_edit.setMaxLength(12)
        self.litros_final_edit.setPlaceholderText('99999999.99')
        self.litros_final_edit.setValidator(QRegExpValidator(QRegExp(r'^\d{1,10}(\.\d{0,2})?$'), self))
        layout.addWidget(self.litros_final_label)
        layout.addWidget(self.litros_final_edit)

        self.add_button = QPushButton('Agregar', self)
        self.add_button.clicked.connect(self.add_historial_entry)
        self.add_button.setStyleSheet("background-color: rgb(88, 129, 216 );")
        layout.addWidget(self.add_button)

        self.finalize_button = QPushButton('Finalizar', self)
        self.finalize_button.clicked.connect(self.finalize_entries)
        self.finalize_button.setStyleSheet("background-color: rgb(88, 129, 216 );")
        layout.addWidget(self.finalize_button)

        self.edit_button = QPushButton('Editar Registro', self)
        self.edit_button.clicked.connect(self.open_edit_window)
        self.edit_button.setStyleSheet("background-color: rgb(88, 129, 216 );")
        layout.addWidget(self.edit_button)

        self.total_litros_label = QLabel('Total de Litros Diesel: 0')
        layout.addWidget(self.total_litros_label)

        self.litros_iniciales_label = QLabel('Litros Iniciales Registrados: 0')
        layout.addWidget(self.litros_iniciales_label)

        self.load_historial_data()

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def open_edit_window(self):
        selected_row = self.historial_table.currentRow()
        if selected_row >= 0:
            folio = self.historial_table.item(selected_row, 0).text()
            self.edit_window = EditHistorialWindow(self, self.db, folio)
            self.edit_window.show()
        else:
            QMessageBox.warning(self, 'Advertencia', 'Seleccione un registro para editar.', QMessageBox.Ok)

    def load_eco_options(self):
        try:
            query = "SELECT eco FROM autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC"
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()

            self.eco_combo.addItem("Seleccionar Eco")
            for row in rows:
                eco_text = str(row[0])
                self.eco_combo.addItem(eco_text)

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar opciones de eco: {e}', QMessageBox.Ok)

    def load_historial_data(self):
        try:
            fecha_actual = QDateTime.currentDateTime().toString('yyyy-MM-dd')
            # Modificar la consulta para ordenar los resultados por folio
            query = """
            SELECT folio, fecha, hora, eco, kilometraje, litros_diesel 
            FROM historial_diesel 
            WHERE fecha = %s 
            ORDER BY folio
            """
            self.db.cursor.execute(query, (fecha_actual,))
            rows = self.db.cursor.fetchall()

            self.historial_table.setRowCount(len(rows))
            total_litros_diesel = 0
            for row_idx, row in enumerate(rows):
                for col_idx, item in enumerate(row):
                    if col_idx == 2:  # La columna de la hora
                        item = item.strftime('%H:%M:%S')  # Formatear hora
                    self.historial_table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))

                litros_diesel = row[5]
                total_litros_diesel += litros_diesel

            self.total_litros_label.setText(f'Total de Litros Diesel: {total_litros_diesel}')

            query_litros_iniciales = "SELECT cuenta_litros_inicial FROM cuenta_litros WHERE fecha = %s"
            self.db.cursor.execute(query_litros_iniciales, (fecha_actual,))
            litros_iniciales = self.db.cursor.fetchall()
            if litros_iniciales:
                total_litros_iniciales = sum([row[0] for row in litros_iniciales])
                self.litros_iniciales_label.setText(f'Litros Iniciales Registrados: {total_litros_iniciales}')
            else:
                self.litros_iniciales_label.setText(f'Litros Iniciales Registrados: 0')

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar datos del historial: {e}', QMessageBox.Ok)

    def add_historial_entry(self):
        try:
            eco = self.eco_combo.currentText()
            kilometraje = self.kilometraje_edit.text()
            litros_diesel = self.litros_diesel_edit.text()

            if not eco or not kilometraje or not litros_diesel:
                QMessageBox.warning(self, 'Advertencia', 'Por favor, complete todos los campos.', QMessageBox.Ok)
                return

            query_insert = """
            INSERT INTO historial_diesel (fecha, eco, kilometraje, litros_diesel)
            VALUES (current_date, %s, %s, %s)
            """
            self.db.cursor.execute(query_insert, (eco, kilometraje, litros_diesel))
            self.db.connection.commit()

            QMessageBox.information(self, 'Éxito', 'Entrada agregada al historial.', QMessageBox.Ok)
            self.load_historial_data()

        except psycopg2.Error as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al agregar entrada: {e}', QMessageBox.Ok)
    
    def finalize_entries(self):
        litros_final = self.litros_final_edit.text()
        if not litros_final:
            QMessageBox.warning(self, 'Advertencia', 'El campo Litros Final es obligatorio.', QMessageBox.Ok)
            return

        try:
            fecha_actual = QDateTime.currentDateTime().toString('yyyy-MM-dd')

            # Obtener el folio
            query_folio = "SELECT nextval('folio_seq_dos')"
            self.db.cursor.execute(query_folio)
            folio = self.db.cursor.fetchone()[0]

            # Actualizar el campo de Litros Final en la tabla cuenta_litros
            query_update = """
            UPDATE cuenta_litros
            SET cuenta_litros_final = %s
            WHERE fecha = %s
            """
            self.db.cursor.execute(query_update, (litros_final, fecha_actual))
            self.db.connection.commit()

            # Consultar los datos de historial_diesel
            query_historial = """
            SELECT folio, fecha, hora, eco, kilometraje, litros_diesel
            FROM historial_diesel
            WHERE fecha = %s
            """
            self.db.cursor.execute(query_historial, (fecha_actual,))
            historial_data = self.db.cursor.fetchall()

            # Calcular la suma de litros_diesel
            suma_litros_diesel = sum(row[5] for row in historial_data)

            # Consultar los datos de cuenta_litros
            query_cuenta_litros = """
            SELECT folio, fecha, cuenta_litros_inicial, cuenta_litros_final
            FROM cuenta_litros
            WHERE fecha = %s
            """
            self.db.cursor.execute(query_cuenta_litros, (fecha_actual,))
            cuenta_litros_data = self.db.cursor.fetchall()

            # Crear un nuevo libro de Excel
            wb = Workbook()
            ws = wb.active
            ws.title = "Historial Diesel"

            # Agregar datos de historial_diesel a la hoja
            headers_historial = ['Folio', 'Fecha', 'Hora', 'Eco', 'Kilometraje', 'Litros Diesel']
            ws.append(headers_historial)
            for row in historial_data:
                ws.append(row)

            # Agregar la suma de litros_diesel
            ws.append([])
            ws.append(['Suma de Litros Diesel', suma_litros_diesel])

            # Agregar datos de cuenta_litros a la hoja
            ws.append([])  # Línea en blanco
            ws.append(['Folio', 'Fecha', 'Cuenta Litros Inicial', 'Cuenta Litros Final', 'Diferencia Litros'])
            for row in cuenta_litros_data:
                diferencia = row[3] - row[2] if row[2] is not None and row[3] is not None else 'N/A'
                ws.append(list(row) + [diferencia])

            # Preguntar al usuario dónde quiere guardar el archivo
            file_path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo Excel", f"historial_suministro_disel_autobuses_{fecha_actual}.xlsx", "Archivos Excel (*.xlsx)")
            if file_path:
                wb.save(file_path)
                QMessageBox.information(self, 'Éxito', f'Historial de diesel finalizado y archivo Excel generado: {file_path}', QMessageBox.Ok)
                self.close()
            else:
                QMessageBox.information(self, 'Cancelado', 'La operación fue cancelada.', QMessageBox.Ok)

        except psycopg2.Error as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al finalizar historial: {e}', QMessageBox.Ok)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
