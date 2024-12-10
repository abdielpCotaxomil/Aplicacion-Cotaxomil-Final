from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
import psycopg2

class InfoTan(QMainWindow):
    def __init__(self, db):
        super(InfoTan, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Información de Historial de Tanque')
        self.setGeometry(200, 200, 800, 600)

        # Tabla para mostrar la información detallada de historial de tanque
        self.tank_table = QTableWidget()
        self.tank_table.setColumnCount(4)  # Número de columnas en la tabla
        self.tank_table.setHorizontalHeaderLabels(['Folio', 'Litros Iniciales', 'Litros Finales', 'Litros Diesel'])
        header = self.tank_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self.tank_table)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        self.load_data()

    def load_data(self):
        try:
            query = "SELECT folio, litros_inicial, litros_final, litros_diesel FROM historial_tanque"
            self.db.cursor.execute(query)
            tank_histories = self.db.cursor.fetchall()

            self.tank_table.setRowCount(len(tank_histories))

            for i, history in enumerate(tank_histories):
                for j, item in enumerate(history):
                    self.tank_table.setItem(i, j, QTableWidgetItem(str(item)))

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar historial de tanque: {e}', QMessageBox.Ok)
