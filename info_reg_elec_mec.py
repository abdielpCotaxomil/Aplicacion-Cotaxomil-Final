from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
import psycopg2

class InfoElecMec(QMainWindow):
    def __init__(self, db):
        super(InfoElecMec, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Información de Historial Electro-Mecánica')
        self.setGeometry(200, 200, 800, 600)

        # Tabla para mostrar la información detallada de historial electro-mecánica
        self.electro_mecanic_table = QTableWidget()
        self.electro_mecanic_table.setColumnCount(8)  # Aumentamos el número de columnas a 8
        self.electro_mecanic_table.setHorizontalHeaderLabels(
            ['Folio', 'Fecha', 'Hora', 'Eco', 'Tipo', 'Kilometraje', 'Descripción', 'Estatus'])
        
        # Ajustar el ancho de la columna 'Descripción'
        self.electro_mecanic_table.setColumnWidth(6, 300)  # Ajusta el ancho de la columna Descripción

        header = self.electro_mecanic_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self.electro_mecanic_table)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        self.electro_mecanic_table.cellClicked.connect(self.show_cell_info)  # Conectar evento de celda clickeada

        self.load_data()

    def load_data(self):
        try:
            query = """
            SELECT h.folio, h.fecha, h.hora, h.eco, 
                   CASE WHEN h.tipo_electro_mecanica = 1 THEN 'Electro' ELSE 'Mecanica' END AS tipo, 
                   COALESCE(k.kilometros, 0) AS kilometraje,  -- Obtener el kilometraje de kilo_eco o 0 si no hay registro
                   h.descripcion, h.estatus 
            FROM historial_electro_mecanica h
            LEFT JOIN kilo_eco k ON h.eco = k.eco  -- Hacemos un LEFT JOIN con la tabla kilo_eco
            WHERE h.estatus = 'ACTIVO'  ORDER BY k.eco ASC
            """
            self.db.cursor.execute(query)
            electro_mecanic_histories = self.db.cursor.fetchall()

            self.electro_mecanic_table.setRowCount(len(electro_mecanic_histories))

            for i, history in enumerate(electro_mecanic_histories):
                for j, item in enumerate(history):
                    self.electro_mecanic_table.setItem(i, j, QTableWidgetItem(str(item)))

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar historial electro-mecánica: {e}', QMessageBox.Ok)

    def show_cell_info(self, row, column):
        try:
            # Obtener el folio de la fila seleccionada
            folio_item = self.electro_mecanic_table.item(row, 0)
            if folio_item:
                folio = folio_item.text()

                # Consultar información detallada para el folio seleccionado
                query = """
                SELECT h.folio, h.fecha, h.hora, h.eco, 
                       CASE WHEN h.tipo_electro_mecanica = 1 THEN 'Electro' ELSE 'Mecanica' END AS tipo, 
                       COALESCE(k.kilometros, 0) AS kilometraje,  -- Mostrar kilometraje
                       h.descripcion, h.estatus 
                FROM historial_electro_mecanica h
                LEFT JOIN kilo_eco k ON h.eco = k.eco
                WHERE h.folio = %s ORDER BY h.eco ASC
                """
                self.db.cursor.execute(query, (folio,))
                details = self.db.cursor.fetchone()

                if details:
                    details_text = '\n'.join([f'{label}: {value}' for label, value in zip(
                        ['Folio', 'Fecha', 'Hora', 'Eco', 'Tipo', 'Kilometraje', 'Descripción', 'Estatus'],
                        details)])
                    QMessageBox.information(self, 'Detalles de Registro', details_text, QMessageBox.Ok)
                else:
                    QMessageBox.warning(self, 'Información', 'No se encontraron detalles para el folio seleccionado.', QMessageBox.Ok)
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al obtener detalles: {e}', QMessageBox.Ok)
