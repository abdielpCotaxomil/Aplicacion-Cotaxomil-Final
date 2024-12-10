import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QFileDialog, QLabel, QMainWindow, QProgressBar, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

def escagris(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def binarizacion(img, umbral):
    _, binary_img = cv2.threshold(img, umbral, 255, cv2.THRESH_BINARY)
    return binary_img

def procesar_mascaras(img, mascaraH, mascaraV):
    Gx = cv2.filter2D(img, -1, np.array(mascaraH))
    Gy = cv2.filter2D(img, -1, np.array(mascaraV))
    
    # Calcular el gradiente
    resultado = np.sqrt(Gx**2 + Gy**2)
    resultado = np.clip(resultado, 0, 255).astype(np.uint8)
    
    return resultado

def create_folders():
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    entrada = os.path.join(desktop, 'prueba_entrada')
    salida = os.path.join(desktop, 'prueba_salida')
    os.makedirs(entrada, exist_ok=True)
    os.makedirs(salida, exist_ok=True)
    return entrada, salida

def compare_images(img1, img2):
    return img1.shape == img2.shape and np.array_equal(img1, img2)

class ImageProcessingThread(QThread):
    progress_updated = pyqtSignal(int)
    processing_finished = pyqtSignal(bool)

    def __init__(self, img_paths):
        super().__init__()
        self.img_paths = img_paths

    def run(self):
        try:
            img1_path, img2_path = self.img_paths
            img1 = cv2.imread(img1_path)
            img2 = cv2.imread(img2_path)
            
            thiningX = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 1.0]]
            thiningY = [[0.0, 1.0, 0.0], [1.0, -4.0, 1.0], [0.0, 1.0, 0.0]]
            pruningX = [[0.0, -1.0, 0.0], [-1.0, 4.0, -1.0], [0.0, -1.0, 0.0]]
            pruningY = [[-1.0, -1.0, -1.0], [-1.0, 8.0, -1.0], [-1.0, -1.0, -1.0]]

            steps = 4
            step = 0

            # Procesar ambas imágenes
            for img, index in [(img1, 1), (img2, 2)]:
                img = escagris(img)
                self.progress_updated.emit(step := step + 1)
                
                img = binarizacion(img, 128)
                self.progress_updated.emit(step := step + 1)

                adelgazada_img = procesar_mascaras(img, thiningX, thiningY)
                self.progress_updated.emit(step := step + 1)

                podada_img = procesar_mascaras(adelgazada_img, pruningX, pruningY)
                self.progress_updated.emit(step := step + 1)

                if index == 1:
                    img1 = podada_img
                else:
                    img2 = podada_img

            # Comparar las imágenes procesadas
            self.processing_finished.emit(compare_images(img1, img2))
        except Exception as e:
            print(f"Error durante el procesamiento: {e}")
            self.processing_finished.emit(False)

class ImageProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procesador de Imágenes")
        self.setGeometry(100, 100, 400, 200)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)
        
        self.button_select_images = QPushButton("Seleccionar Imágenes")
        self.button_select_images.clicked.connect(self.select_images)
        self.layout.addWidget(self.button_select_images)

        self.button_start_processing = QPushButton("Iniciar Procesamiento")
        self.button_start_processing.clicked.connect(self.start_processing)
        self.layout.addWidget(self.button_start_processing)

        self.image_paths = []
        self.thread = None

    def select_images(self):
        entrada, _ = create_folders()
        self.image_paths, _ = QFileDialog.getOpenFileNames(self, "Seleccionar Imágenes", entrada, "Imágenes (*.png *.jpg *.tif)")
        if len(self.image_paths) < 2:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar dos imágenes.")
            return

    def start_processing(self):
        if len(self.image_paths) != 2:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar dos imágenes.")
            return
        
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(8)

        self.thread = ImageProcessingThread(self.image_paths)
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.processing_finished.connect(self.processing_finished)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def processing_finished(self, result):
        msg = "Las huellas coinciden" if result else "Las huellas no coinciden"
        QMessageBox.information(self, "Resultado", msg)

if __name__ == "__main__":
    app = QApplication([])
    window = ImageProcessor()
    window.show()
    app.exec_()