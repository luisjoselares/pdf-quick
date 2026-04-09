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
        """
        Elimina el fondo enviando la imagen a la API de Hugging Face.
        Incluye lógica de espera para el modelo y limpieza de RAM.
        """
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "X-Wait-For-Model": "true" 
        }
        
        try:
            # Petición a la API externa
            response = requests.post(
                ImageController.API_URL, 
                headers=headers, 
                data=file_bytes,
                timeout=60 
            )
            
            # Si hay error (4xx o 5xx), lanza una excepción
            response.raise_for_status() 
            
            # Guardamos el resultado en un buffer
            result = io.BytesIO(response.content)
            
            # Limpieza inmediata de la respuesta para liberar RAM
            del response
            gc.collect()
            
            return result

        except requests.exceptions.Timeout:
            gc.collect()
            raise Exception("La IA tardó demasiado en responder. Inténtalo con una imagen más pequeña.")
        except requests.exceptions.RequestException as e:
            gc.collect()
            raise Exception(f"Error de conexión con la IA: {str(e)}")
        except Exception as e:
            gc.collect()
            raise e

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
