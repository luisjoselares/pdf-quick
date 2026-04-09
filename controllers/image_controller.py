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
        # Cabeceras con el parámetro 'wait_for_model'
        # Esto obliga a la API a esperar que el modelo cargue antes de responder
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "X-Wait-For-Model": "true" 
        }
        
        try:
            # Añadimos un timeout de 60 segundos para darle tiempo a procesar
            response = requests.post(
                ImageController.API_URL, 
                headers=headers, 
                data=file_bytes,
                timeout=60 
            )
            
            # Verificamos si la respuesta fue exitosa
            response.raise_for_status() 
            
            return io.BytesIO(response.content)

        except requests.exceptions.Timeout:
            raise Exception("La IA tardó demasiado en responder. Inténtalo con una imagen más pequeña.")
        except requests.exceptions.RequestException as e:
            # Si el error es el IncompleteRead, suele ser capturado aquí
            raise Exception(f"Error de conexión con la IA: {str(e)}")

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
