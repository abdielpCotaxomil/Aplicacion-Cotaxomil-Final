from PIL import Image

# Cargar la imagen para obtener sus dimensiones
image_path = 'path_to_image/Final Camion.png'
image = Image.open(image_path)
width, height = image.size

width, height