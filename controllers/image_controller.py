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
        # 1. Cabeceras reforzadas para evitar desconexiones
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "X-Wait-For-Model": "true",
            "Connection": "close"  # Crucial: evita que el socket quede abierto y se corrompa
        }
        
        try:
            # 2. Aseguramos que file_bytes sea un objeto de bytes puro
            if isinstance(file_bytes, io.BytesIO):
                data = file_bytes.getvalue()
            else:
                data = file_bytes

            # 3. Petición directa sin Session para resetear el socket en cada llamada
            response = requests.post(
                ImageController.API_URL, 
                headers=headers, 
                data=data,
                timeout=60
            )
            
            # 4. Si el error es 503, es que el modelo aún carga
            if response.status_code == 503:
                raise Exception("La IA se está despertando. Reintenta en 10 segundos.")
                
            response.raise_for_status() 
            
            # 5. Verificación de integridad del contenido
            if len(response.content) < 100: # Un PNG real no pesa menos que esto
                raise Exception("Respuesta de IA incompleta o inválida.")

            result = io.BytesIO(response.content)
            
            # Limpieza
            del response
            gc.collect()
            
            return result

        except requests.exceptions.ConnectionError:
            gc.collect()
            raise Exception("Fallo de red. Hugging Face rechazó la conexión. Reintenta.")
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
