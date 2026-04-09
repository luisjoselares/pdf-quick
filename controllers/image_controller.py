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
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "X-Wait-For-Model": "true",
            "X-Use-Cache": "false" # Forzamos a que no use caché para evitar datos corruptos
        }
        
        try:
            # Forzamos que los bytes se lean desde el principio
            if hasattr(file_bytes, 'seek'):
                file_bytes.seek(0)
            
            # Usamos un bloque with para asegurar que la conexión se cierre al terminar
            with requests.Session() as session:
                # Quitamos el 'Content-Type' manual para que requests lo maneje 
                # o enviamos los bytes directamente sin streaming
                response = session.post(
                    ImageController.API_URL, 
                    headers=headers, 
                    data=file_bytes,
                    timeout=(10, 60), # (Connection timeout, Read timeout)
                    stream=False
                )
                
                response.raise_for_status()
                
                # Leemos todo el contenido de una vez
                content = response.content
                if not content:
                    raise Exception("La API devolvió un archivo vacío.")
                
                result = io.BytesIO(content)
                del content
                gc.collect()
                return result

        except requests.exceptions.ChunkedEncodingError:
            raise Exception("La conexión se interrumpió. Intenta con una imagen más pequeña.")
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
