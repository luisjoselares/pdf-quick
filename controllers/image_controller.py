import io
import os
import requests
from PIL import Image

class ImageController:
    # URL del modelo en Hugging Face (RMBG-1.4 es excelente y rápido)
    API_URL = "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
    
    # El Token lo configuraremos en Render como variable de entorno
    HF_TOKEN = os.environ.get("HF_TOKEN")

    @staticmethod
    def remove_background(file_bytes):
        headers = {"Authorization": f"Bearer {ImageController.HF_TOKEN}"}
        
        # Enviamos la imagen al servidor de Hugging Face
        response = requests.post(ImageController.API_URL, headers=headers, data=file_bytes)
        
        # Si el modelo se está cargando, Hugging Face devuelve un 503
        if response.status_code == 200:
            return io.BytesIO(response.content)
        elif response.status_code == 503:
            raise Exception("La IA se está despertando. Inténtalo de nuevo en 20 segundos.")
        else:
            raise Exception(f"Error en la IA: {response.text}")

    @staticmethod
    def upscale_image(file_bytes, factor=2):
        # El escalado lo dejamos local porque Pillow es muy ligero (usa poca RAM)
        img = Image.open(io.BytesIO(file_bytes))
        w, h = img.size
        new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
        
        out = io.BytesIO()
        new_img.save(out, format="PNG")
        out.seek(0)
        return out
