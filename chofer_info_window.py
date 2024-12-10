from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel

class ChoferInfoWindow(QDialog):
    def __init__(self, chofer_data, parent=None):
        super(ChoferInfoWindow, self).__init__(parent)
        self.chofer_data = chofer_data
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Información del Chofer')
        layout = QVBoxLayout()

        for key, value in self.chofer_data.items():
            label = QLabel(f"{key}: {value}")
            layout.addWidget(label)

        self.setLayout(layout)
