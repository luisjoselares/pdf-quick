import io
import os
import requests
import gc
from PIL import Image

class ImageController:
    # URL del modelo en Hugging Face (RMBG-1.4 es excelente y rápido)
    API_URL = "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
    
    # El Token se obtiene de las variables de entorno de Render
    HF_TOKEN = os.environ.get("HF_TOKEN")

   @staticmethod
    def remove_background(file_bytes):
        # Cabeceras reforzadas
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "X-Wait-For-Model": "true",
            "Content-Type": "image/png" # Forzamos el tipo de contenido
        }
        
        try:
            # Usamos una sesión para mantener la conexión más estable
            session = requests.Session()
            response = session.post(
                ImageController.API_URL, 
                headers=headers, 
                data=file_bytes,
                timeout=60,
                stream=False # Cambiamos a False para asegurar lectura completa
            )
            
            response.raise_for_status() 
            result = io.BytesIO(response.content)
            
            del response
            gc.collect()
            return result
            
    @staticmethod
    def upscale_image(file_bytes, factor=2):
        """
        Aumenta el tamaño de la imagen localmente usando Pillow.
        Es ligero y no requiere API externa.
        """
        try:
            # Cargamos la imagen en memoria
            img = Image.open(io.BytesIO(file_bytes))
            
            # Calculamos nuevas dimensiones
            w, h = img.size
            # Escalado de alta calidad (Lanczos)
            new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
            
            out = io.BytesIO()
            new_img.save(out, format="PNG")
            out.seek(0)

            # --- Limpieza Profunda ---
            img.close()
            del img
            del new_img
            gc.collect() # Forzamos liberación de RAM basura
            
            return out

        except Exception as e:
            gc.collect()
            raise Exception(f"Error al escalar la imagen: {str(e)}")
