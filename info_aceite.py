from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QLabel, QHBoxLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import psycopg2

class InfoAceite(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Lista de Historial de Cambios de Aceite")
        self.resize(350, 350)

        self.layout = QVBoxLayout()
        
        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)

        # Botón para verificar los cambios de aceite
        self.nv_aceite_btn = QPushButton('NV de aceite', self)
        self.nv_aceite_btn.clicked.connect(self.check_aceite)
        self.nv_aceite_btn.setStyleSheet("background-color: rgb(131, 190, 32 );")
        self.layout.addWidget(self.nv_aceite_btn)

        self.setLayout(self.layout)

    def check_aceite(self):
        try:
            # Consulta para obtener los ecos y kilometraje
            query = """
            SELECT eco, kilometros 
            FROM kilo_eco ORDER BY eco ASC
            """
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()

            self.list_widget.clear()  # Limpiar la lista antes de agregar nuevos elementos
            for row in rows:
                eco = row[0]
                kilometraje = row[1]

                # Crear un widget personalizado con QLabel para poder cambiar los colores
                item_widget = QWidget()
                item_layout = QHBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)
                
                item_label = QLabel(f"Eco: {eco} - Kilometraje: {kilometraje} - ")
                aviso_label = QLabel()

                # Verificar si el kilometraje es múltiplo de 30,000 o cercano a ello
                if kilometraje >= 30000 and kilometraje % 30000 <= 1000:
                    aviso_label.setText("Cambio de aceite")
                    aviso_label.setStyleSheet("color: red;")
                elif kilometraje % 30000 >= 20000 and kilometraje % 30000 < 30000:
                    aviso_label.setText("Pendiente")
                    aviso_label.setStyleSheet("color: orange;")
                else:
                    aviso_label.setText("Sin necesidad de cambio")
                    aviso_label.setStyleSheet("color: blue;")

                # Añadir los labels al layout
                item_layout.addWidget(item_label)
                item_layout.addWidget(aviso_label)

                item_widget.setLayout(item_layout)
                
                # Añadir el widget personalizado a la lista
                list_item = QListWidgetItem(self.list_widget)
                list_item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, item_widget)

        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'Error al consultar los cambios de aceite: {e}', QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error inesperado: {e}', QMessageBox.Ok)

