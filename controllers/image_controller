import io
from rembg import remove
from PIL import Image

class ImageController:
    @staticmethod
    def remove_background(file_bytes):
        input_image = Image.open(io.BytesIO(file_bytes))
        # rembg hace el trabajo pesado aquí
        output_image = remove(input_image)
        
        out = io.BytesIO()
        output_image.save(out, format="PNG")
        out.seek(0)
        return out

    @staticmethod
    def upscale_image(file_bytes, factor=2):
        img = Image.open(io.BytesIO(file_bytes))
        w, h = img.size
        # Escalado Lanczos: es rápido y da mucha nitidez sin pesar GBs en el servidor
        new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
        
        out = io.BytesIO()
        new_img.save(out, format="PNG")
        out.seek(0)
        return out
