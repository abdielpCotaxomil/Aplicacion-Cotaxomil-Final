from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QFileDialog
import psycopg2
import pandas as pd

class InfoArrElecMec(QMainWindow):
    def __init__(self, db):
        super(InfoArrElecMec, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Información de Historial Electro-Mecánica')
        self.setGeometry(200, 200, 800, 600)

        # Fecha de inicio
        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))  # Fecha por defecto un mes atrás
        self.start_date_edit.setCalendarPopup(True)

        # Fecha de fin
        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setDate(QDate.currentDate())  # Fecha por defecto hoy
        self.end_date_edit.setCalendarPopup(True)

        # Botón para cargar datos
        self.load_data_btn = QPushButton('Cargar Datos', self)
        self.load_data_btn.clicked.connect(self.load_data)
        self.load_data_btn.setStyleSheet("background-color: rgb(131, 190, 32 );")

        # Layout de fechas y botón
        date_layout = QHBoxLayout()
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(self.end_date_edit)
        date_layout.addWidget(self.load_data_btn)

        # Tabla para mostrar la información detallada de historial electro-mecánica
        self.electro_mecanic_table = QTableWidget()
        self.electro_mecanic_table.setColumnCount(9)  # Número de columnas en la tabla
        self.electro_mecanic_table.setHorizontalHeaderLabels(
            ['Folio', 'Fecha', 'Hora', 'Eco', 'Tipo', 'Descripción', 'Estatus', 'Empleado', 'Arreglo'])
        
        # Ajustar el ancho de las columnas 'Descripción' y 'Arreglo'
        self.electro_mecanic_table.setColumnWidth(5, 600)  # Ajustar ancho de columna 'Descripción'
        self.electro_mecanic_table.setColumnWidth(8, 400)  # Ajustar ancho de columna 'Arreglo'

        header = self.electro_mecanic_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Botón para generar Excel
        self.export_excel_btn = QPushButton('Generar Excel', self)
        self.export_excel_btn.setStyleSheet("background-color: rgb(131, 190, 32 );")
        self.export_excel_btn.clicked.connect(self.export_to_excel)

        layout = QVBoxLayout()
        layout.addLayout(date_layout)
        layout.addWidget(self.electro_mecanic_table)
        layout.addWidget(self.export_excel_btn)  # Añadir botón de exportar a Excel al layout

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        self.electro_mecanic_table.cellClicked.connect(self.show_cell_info)  # Conectar evento de celda clickeada

    def load_data(self):
        try:
            self.start_date = self.start_date_edit.date().toString('yyyy-MM-dd')
            self.end_date = self.end_date_edit.date().toString('yyyy-MM-dd')

            query = """
            SELECT folio, fecha, hora, eco, 
                   CASE WHEN tipo_electro_mecanica = 1 THEN 'Electro' ELSE 'Mecanica' END AS tipo, 
                   descripcion, estatus, id_empleado, arreglo 
            FROM historial_electro_mecanica 
            WHERE estatus = 'RESUELTO' AND fecha BETWEEN %s AND %s
            ORDER BY eco ASC
            """
            self.db.cursor.execute(query, (self.start_date, self.end_date))
            self.electro_mecanic_histories = self.db.cursor.fetchall()

            self.electro_mecanic_table.setRowCount(len(self.electro_mecanic_histories))

            for i, history in enumerate(self.electro_mecanic_histories):
                for j, item in enumerate(history):
                    self.electro_mecanic_table.setItem(i, j, QTableWidgetItem(str(item)))

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar historial electro-mecánica: {e}', QMessageBox.Ok)

    def export_to_excel(self):
        try:
            # Convertir los datos a un DataFrame de pandas
            df = pd.DataFrame(self.electro_mecanic_histories, columns=['Folio', 'Fecha', 'Hora', 'Eco', 'Tipo', 'Descripción', 'Estatus', 'Empleado', 'Arreglo'])

            # Abrir el diálogo para que el usuario elija el directorio donde guardar el archivo
            options = QFileDialog.Options()
            options |= QFileDialog.ShowDirsOnly  # Mostrar solo carpetas
            directory = QFileDialog.getExistingDirectory(self, "Seleccionar directorio", "", options=options)

            if directory:  # Verificar que el usuario seleccionó un directorio
                # Construir el nombre del archivo con la ruta seleccionada y el nombre fijo
                output_path = f'{directory}/historial_electro_mecanica_{self.start_date}_a_{self.end_date}.xlsx'

                # Guardar el DataFrame en un archivo Excel
                with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Historial')

                    # Obtener el objeto workbook y worksheet
                    workbook  = writer.book
                    worksheet = writer.sheets['Historial']

                    # Ajustar el ancho de las columnas 'Descripción' y 'Arreglo' en Excel
                    worksheet.set_column('F:F', 40)  # Ajustar ancho de columna 'Descripción'
                    worksheet.set_column('I:I', 30)  # Ajustar ancho de columna 'Arreglo'

                QMessageBox.information(self, 'Éxito', 'El archivo Excel ha sido generado y guardado correctamente.', QMessageBox.Ok)
            else:
                QMessageBox.warning(self, 'Cancelado', 'La operación fue cancelada.', QMessageBox.Ok)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error al generar el archivo Excel: {e}', QMessageBox.Ok)

    def show_cell_info(self, row, column):
        try:
            # Obtener el folio de la fila seleccionada
            folio_item = self.electro_mecanic_table.item(row, 0)
            if folio_item:
                folio = folio_item.text()

                # Consultar información detallada para el folio seleccionado
                query = """
                SELECT folio, fecha, hora, eco, 
                       CASE WHEN tipo_electro_mecanica = 1 THEN 'Electro' ELSE 'Mecanica' END AS tipo, 
                       descripcion, estatus, id_empleado, arreglo 
                FROM historial_electro_mecanica 
                WHERE folio = %s
                """
                self.db.cursor.execute(query, (folio,))
                details = self.db.cursor.fetchone()

                if details:
                    details_text = '\n'.join([f'{label}: {value}' for label, value in zip(
                        ['Folio', 'Fecha', 'Hora', 'Eco', 'Tipo', 'Descripción', 'Estatus', 'Empleado', 'Arreglo'],
                        details)])
                    QMessageBox.information(self, 'Detalles de Registro', details_text, QMessageBox.Ok)
                else:
                    QMessageBox.warning(self, 'Información', 'No se encontraron detalles para el folio seleccionado.', QMessageBox.Ok)
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al obtener detalles: {e}', QMessageBox.Ok)
