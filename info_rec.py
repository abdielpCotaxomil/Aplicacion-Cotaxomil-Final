from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
import psycopg2

class InfoRec(QMainWindow):
    def __init__(self, db):
        super(InfoRec, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Información de Recaudos')
        self.setGeometry(200, 200, 800, 600)

        # Tabla para mostrar la información detallada de recaudos
        self.recaudo_table = QTableWidget()
        self.recaudo_table.setColumnCount(9)  # Incrementar el número de columnas para el total
        self.recaudo_table.setHorizontalHeaderLabels(
            ['Folio', 'Fecha', 'Hora', 'Eco', 'ID Chofer 1', 'ID Chofer 2', 'Monedas', 'Billetes', 'Total'])
        header = self.recaudo_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self.recaudo_table)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        self.load_data()

    def load_data(self):
        try:
            query = "SELECT folio, fecha, hora, eco, id_chofer1, id_chofer2, monedas, billetes FROM historial_recaudo ORDER BY folio ASC"
            self.db.cursor.execute(query)
            recaudos = self.db.cursor.fetchall()

            self.recaudo_table.setRowCount(len(recaudos) + 1)  # Añadir una fila adicional para el total

            total_monedas = 0
            total_billetes = 0

            for i, recaudo in enumerate(recaudos):
                for j, item in enumerate(recaudo):
                    self.recaudo_table.setItem(i, j, QTableWidgetItem(str(item)))

                # Calcular total de monedas y billetes
                try:
                    monedas = float(recaudo[6]) if recaudo[6] else 0
                    billetes = float(recaudo[7]) if recaudo[7] else 0
                    total_monedas += monedas
                    total_billetes += billetes
                    total = monedas + billetes
                    self.recaudo_table.setItem(i, 8, QTableWidgetItem(str(total)))
                except ValueError:
                    self.recaudo_table.setItem(i, 8, QTableWidgetItem('Error'))

            # Mostrar el total en la última fila
            self.recaudo_table.setItem(len(recaudos), 7, QTableWidgetItem(f'Total'))
            self.recaudo_table.setItem(len(recaudos), 8, QTableWidgetItem(f'{total_monedas + total_billetes}'))

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar recaudos: {e}', QMessageBox.Ok)
