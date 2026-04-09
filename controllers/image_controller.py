import io
import os
import requests
import gc
from PIL import Image

class ImageController:
    # URL del modelo en Hugging Face
    API_URL = "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
    
    # El Token se obtiene de las variables de entorno de Render
    HF_TOKEN = os.environ.get("HF_TOKEN")

    @staticmethod
    def remove_background(file_bytes):
        """
        Elimina el fondo enviando la imagen a la API de Hugging Face.
        """
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "X-Wait-For-Model": "true",
            "Content-Type": "image/png"
        }
        
        try:
            # Usamos una sesión para mayor estabilidad
            session = requests.Session()
            response = session.post(
                ImageController.API_URL, 
                headers=headers, 
                data=file_bytes,
                timeout=60 
            )
            
            response.raise_for_status() 
            result = io.BytesIO(response.content)
            
            # Limpieza de RAM inmediata
            del response
            gc.collect()
            
            return result

        except Exception as e:
            gc.collect()
            raise e

    @staticmethod
    def upscale_image(file_bytes, factor=2):
        """
        Aumenta el tamaño de la imagen localmente usando Pillow.
        """
        try:
            img = Image.open(io.BytesIO(file_bytes))
            w, h = img.size
            new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
            
            out = io.BytesIO()
            new_img.save(out, format="PNG")
            out.seek(0)

            # Limpieza Profunda
            img.close()
            del img
            del new_img
            gc.collect() 
            
            return out

        except Exception as e:
            gc.collect()
            raise Exception(f"Error al escalar: {str(e)}")
