from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt
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

class DelPatForm(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Lista de Empleados")
        self.setStyleSheet("font-size: 16px;")  # Aplicar tamaño de fuente general
        self.resize(600, 600)


        self.layout = QVBoxLayout()
        
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Buscar empleado...")
        self.search_bar.textChanged.connect(self.update_search_results)
        self.layout.addWidget(self.search_bar)

        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("font-size: 16px;")  # Tamaño de fuente en la lista
        self.layout.addWidget(self.list_widget)

        self.load_data_btn = QPushButton('Cargar Datos', self)
        self.load_data_btn.setStyleSheet("font-size: 16px;")  # Tamaño de fuente en el botón
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
                item_label.setStyleSheet("font-size: 16px;")  # Tamaño de fuente en la etiqueta
                item_label.setFixedHeight(25)

                delete_btn = QPushButton("Eliminar")
                delete_btn.setStyleSheet("background-color: rgb(255, 0, 0); font-size: 16px;")  # Tamaño de fuente en el botón
                delete_btn.setFixedSize(100, 50)
                delete_btn.clicked.connect(lambda ch, row=row: self.delete_item(row[0]))
                
                item_layout.addWidget(item_label)
                item_layout.addWidget(delete_btn)
                
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

    def delete_item(self, item_id):
        try:
            reply = QMessageBox.question(self, 'Eliminar Empleado', 
                                         '¿Estás seguro de que quieres eliminar este Empleado?', 
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                query = "DELETE FROM empleado_patio WHERE num_empleado = %s"
                self.db.cursor.execute(query, (item_id,))
                self.db.connection.commit()
                QMessageBox.information(self, 'Éxito', 'Empleado eliminado correctamente', QMessageBox.Ok)
                self.load_data()  # Recargar los datos después de la eliminación

        except psycopg2.Error as e:
            self.db.connection.rollback()
            print(f"Error durante la eliminación del Empleado: {e}")
            QMessageBox.critical(self, 'Error', f'No se pudo eliminar el Empleado: {e}', QMessageBox.Ok)
        except Exception as e:
            print(f"Error inesperado: {e}")
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)
