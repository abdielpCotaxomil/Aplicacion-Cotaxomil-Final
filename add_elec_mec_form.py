from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QTextEdit, QMessageBox, QLineEdit
from PyQt5.QtCore import QDateTime
import psycopg2

class AddElecMecForm(QMainWindow):
    def __init__(self, db):
        super(AddElecMecForm, self).__init__()
        self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Agregar Historial Electro-Mecánica')
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.folio_label = QLabel('Folio: Generado automáticamente')
        layout.addWidget(self.folio_label)

        self.eco_label = QLabel('Eco:')
        self.eco_combo = QComboBox(self)
        layout.addWidget(self.eco_label)
        layout.addWidget(self.eco_combo)
        self.load_eco()

        self.tipo_label = QLabel('Tipo:')
        self.tipo_combo = QComboBox(self)
        self.tipo_combo.addItems(['Electro', 'Mecanica'])
        layout.addWidget(self.tipo_label)
        layout.addWidget(self.tipo_combo)

     # Nuevo campo para ingresar el kilometraje
        self.kilometraje_label = QLabel('Kilometraje:')
        self.kilometraje_edit = QLineEdit(self)
        layout.addWidget(self.kilometraje_label)
        layout.addWidget(self.kilometraje_edit)

        self.descripcion_label = QLabel('Descripción:')
        self.descripcion_edit = QTextEdit(self)
        layout.addWidget(self.descripcion_label)
        layout.addWidget(self.descripcion_edit)

 

        self.add_button = QPushButton('GUARDAR', self)
        self.add_button.clicked.connect(self.save_electro_mecanic_history)
        self.add_button.setStyleSheet("background-color: rgb(131, 190, 32 );")
        layout.addWidget(self.add_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

    def load_eco(self):
        try:
            query = "SELECT eco FROM autobus WHERE estatus = 'ACTIVO' ORDER BY eco ASC"
            self.db.cursor.execute(query)
            ecos = self.db.cursor.fetchall()
            for eco in ecos:
                self.eco_combo.addItem(str(eco[0]))
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al cargar ecos: {e}', QMessageBox.Ok)

    def save_electro_mecanic_history(self):
        eco = self.eco_combo.currentText()
        tipo = self.tipo_combo.currentText()
        descripcion = self.descripcion_edit.toPlainText()
        fecha_hora = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        kilometraje = self.kilometraje_edit.text()

        if not kilometraje:
            QMessageBox.critical(self, 'Error', 'El campo de kilometraje no puede estar vacío.', QMessageBox.Ok)
            return

        # Convertir tipo a número
        tipo_num = 1 if tipo == 'Electro' else 2

        try:
            # Obtener el folio
            query_folio = "SELECT nextval('folio_seq_seis')"
            self.db.cursor.execute(query_folio)
            folio = self.db.cursor.fetchone()[0]

            # Insertar en historial_electro_mecanica
            query_insert = """
            INSERT INTO historial_electro_mecanica (folio, fecha, hora, eco, tipo_electro_mecanica, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            fecha, hora = fecha_hora.split(' ')
            self.db.cursor.execute(query_insert, (folio, fecha, hora, eco, tipo_num, descripcion))

            # Insertar o actualizar kilometraje en kilo_eco
            query_kilometraje = """
            INSERT INTO kilo_eco (eco, kilometros) 
            VALUES (%s, %s) 
            ON CONFLICT (eco) 
            DO UPDATE SET kilometros = EXCLUDED.kilometros
            """
            self.db.cursor.execute(query_kilometraje, (eco, kilometraje))

            # Confirmar ambas operaciones
            self.db.connection.commit()

            QMessageBox.information(self, 'Éxito', 'Historial electro-mecánica y kilometraje agregado correctamente.', QMessageBox.Ok)
            self.close()

        except psycopg2.Error as e:
            # Deshacer transacciones si ocurre un error en la base de datos
            self.db.connection.rollback()
            QMessageBox.critical(self, 'Error', f'Error al agregar historial electro-mecánica: {e}', QMessageBox.Ok)

        except Exception as e:
            # Manejar cualquier otro error inesperado
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
