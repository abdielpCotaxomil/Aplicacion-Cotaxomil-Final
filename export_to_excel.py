import pandas as pd
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import QDateTime

def export_historial_to_excel(db, fecha_inicio, hora_inicio, fecha_fin, hora_fin):
    try:
        query = """
        SELECT folio, fecha, hora, eco, kilometraje, litros_diesel
        FROM historial_diesel
        WHERE fecha BETWEEN %s AND %s
        AND hora BETWEEN %s AND %s
        """
        db.cursor.execute(query, (fecha_inicio, fecha_fin, hora_inicio, hora_fin))
        rows = db.cursor.fetchall()

        df = pd.DataFrame(rows, columns=['Folio', 'Fecha', 'Hora', 'Eco', 'Kilometraje', 'Litros Diesel'])

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(None, "Guardar archivo Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_path:
            df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(None, 'Éxito', 'Datos exportados a Excel exitosamente.', QMessageBox.Ok)

    except Exception as e:
        QMessageBox.critical(None, 'Error', f'Error al exportar a Excel: {e}', QMessageBox.Ok)

def get_date_range():
    dialog = QDateTimeDialog()
    if dialog.exec_():
        fecha_inicio = dialog.fecha_inicio_edit.text()
        hora_inicio = dialog.hora_inicio_edit.text()
        fecha_fin = dialog.fecha_fin_edit.text()
        hora_fin = dialog.hora_fin_edit.text()
        return fecha_inicio, hora_inicio, fecha_fin, hora_fin, True
    return '', '', '', '', False

class QDateTimeDialog(QDialog):
    def __init__(self, parent=None):
        super(QDateTimeDialog, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Seleccionar Rango de Fechas y Horas')

        layout = QVBoxLayout()

        self.fecha_inicio_label = QLabel('Fecha Inicio (YYYY-MM-DD):')
        self.fecha_inicio_edit = QLineEdit(self)
        layout.addWidget(self.fecha_inicio_label)
        layout.addWidget(self.fecha_inicio_edit)

        self.hora_inicio_label = QLabel('Hora Inicio (HH:MM:SS):')
        self.hora_inicio_edit = QLineEdit(self)
        layout.addWidget(self.hora_inicio_label)
        layout.addWidget(self.hora_inicio_edit)

        self.fecha_fin_label = QLabel('Fecha Fin (YYYY-MM-DD):')
        self.fecha_fin_edit = QLineEdit(self)
        layout.addWidget(self.fecha_fin_label)
        layout.addWidget(self.fecha_fin_edit)

        self.hora_fin_label = QLabel('Hora Fin (HH:MM:SS):')
        self.hora_fin_edit = QLineEdit(self)
        layout.addWidget(self.hora_fin_label)
        layout.addWidget(self.hora_fin_edit)

        self.ok_button = QPushButton('OK', self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)
