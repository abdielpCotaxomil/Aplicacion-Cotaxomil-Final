import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QFormLayout, QTextEdit, QMessageBox, QHBoxLayout, QLabel, QComboBox
from PyQt5.QtCore import Qt
import psycopg2

class DatabaseConnection:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="tu_db",
            user="tu_usuario",
            password="tu_contraseña",
            host="localhost"
        )
        self.cursor = self.connection.cursor()

class ArrElecMec(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Lista de Historial Electro-Mecánica")
        self.resize(350, 350)

        self.layout = QVBoxLayout()
        
        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)

        self.load_data_btn = QPushButton('Cargar Datos', self)
        self.load_data_btn.clicked.connect(self.load_data)
        self.load_data_btn.setStyleSheet("background-color: rgb(131, 190, 32 );")
        self.layout.addWidget(self.load_data_btn)

        self.setLayout(self.layout)

    def load_data(self):
        try:
            query = """
            SELECT folio, 
                   CASE WHEN tipo_electro_mecanica = 1 THEN 'Electro' ELSE 'Mecanica' END AS tipo, 
                   descripcion 
            FROM historial_electro_mecanica 
            WHERE estatus = 'ACTIVO'
            ORDER BY eco ASC
            """
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()

            self.list_widget.clear()
            for row in rows:
                item_widget = QWidget()
                item_layout = QHBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)
                
                item_text = f"{row[0]} - {row[1]} - {row[2]}"
                item_label = QLabel(item_text)
                item_label.setFixedHeight(25)

                arreglar_btn = QPushButton("Arreglar")
                arreglar_btn.setFixedSize(60, 16)
                arreglar_btn.clicked.connect(lambda ch, row=row: self.edit_item(row[0], row[2]))
                arreglar_btn.setStyleSheet("background-color: rgb(131, 190, 32 );")
                
                item_layout.addWidget(item_label)
                item_layout.addWidget(arreglar_btn)
                
                item_widget.setLayout(item_layout)
                
                list_item = QListWidgetItem(self.list_widget)
                list_item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, item_widget)
                
        except Exception as e:
            print(f"Error al cargar los datos: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar los datos: {e}', QMessageBox.Ok)

    def edit_item(self, folio, descripcion):
        self.edit_window = EditWindow(self.db, folio, descripcion)
        self.edit_window.show()

class EditWindow(QWidget):
    def __init__(self, db, folio, descripcion, parent=None):
        super().__init__(parent)
        self.db = db
        self.folio = folio
        self.setWindowTitle("Editar Descripción")

        self.layout = QFormLayout()
        
        self.descripcion = QTextEdit(self)
        self.descripcion.setText(descripcion)
        self.layout.addRow('Descripción:', self.descripcion)

        self.empleado_combo = QComboBox(self)
        self.load_empleados()
        self.layout.addRow('Empleado:', self.empleado_combo)

        self.update_btn = QPushButton('Actualizar', self)
        self.update_btn.clicked.connect(self.update_data)
        self.update_btn.setStyleSheet("background-color: rgb(131, 190, 32 );")
        self.layout.addWidget(self.update_btn)

        self.setLayout(self.layout)

    def load_empleados(self):
        try:
            query = """
            SELECT num_empleado, nombre, apellido_paterno, apellido_materno
            FROM empleado_patio
            WHERE puesto IN ('MECANICO', 'ELECTRICO')
            """
            self.db.cursor.execute(query)
            empleados = self.db.cursor.fetchall()
            for emp in empleados:
                self.empleado_combo.addItem(f"{emp[0]} - {emp[1]} {emp[2]} {emp[3]}", emp[0])
        except Exception as e:
            print(f"Error al cargar empleados: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudieron cargar los empleados: {e}', QMessageBox.Ok)

    def update_data(self):
        try:
            nueva_descripcion = self.descripcion.toPlainText()
            num_empleado = self.empleado_combo.currentData()

            if not nueva_descripcion:
                QMessageBox.critical(self, 'Error', 'La descripción no puede estar vacía', QMessageBox.Ok)
                return

            query = """
            UPDATE historial_electro_mecanica
            SET estatus = 'RESUELTO', id_empleado = %s, arreglo = %s
            WHERE folio = %s
            """
            # Nota: 'folio' debe ser un entero, 'num_empleado' y 'arreglo' son cadenas.
            self.db.cursor.execute(query, (num_empleado, nueva_descripcion, self.folio))
            self.db.connection.commit()  # Confirmar los cambios

            QMessageBox.information(self, 'Éxito', 'Datos actualizados correctamente', QMessageBox.Ok)
            self.close()

        except psycopg2.Error as e:
            self.db.connection.rollback()  # Revertir los cambios en caso de error
            print(f"Error durante la actualización del query: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudo actualizar el historial: {e}', QMessageBox.Ok)
        except Exception as e:
            print(f"Error inesperado: {e}")
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
