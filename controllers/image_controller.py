import io
import os
import requests
import gc
from PIL import Image
import base64

class ImageController:
    # URL del modelo en Hugging Face
    API_URL = "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
    
    # El Token se obtiene de las variables de entorno de Render
    HF_TOKEN = os.environ.get("HF_TOKEN")

    @staticmethod
    def remove_background(file_bytes):
        import base64  # Necesario para el transporte estable
        
        # 1. Convertimos los bytes de la imagen a una cadena Base64
        # Esto evita que la conexión se rompa por enviar datos binarios crudos
        img_64 = base64.b64encode(file_bytes).decode('utf-8')
        
        # 2. Preparamos el payload estilo JSON (más robusto para la API)
        payload = {
            "inputs": img_64,
            "parameters": {"wait_for_model": True}
        }
        
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "Content-Type": "application/json",
            "Connection": "close" 
        }
        
        try:
            # 3. Petición POST enviando JSON
            response = requests.post(
                ImageController.API_URL, 
                headers=headers, 
                json=payload, # Enviamos como JSON
                timeout=60
            )
            
            # Si el modelo está cargando (503), avisamos
            if response.status_code == 503:
                raise Exception("La IA se está despertando. Reintenta en 15 segundos.")
            
            response.raise_for_status()
            
            # 4. Hugging Face suele devolver la imagen procesada en binario
            # Verificamos que tengamos contenido real
            if not response.content or len(response.content) < 100:
                raise Exception("La respuesta de la IA está vacía o es inválida.")

            result = io.BytesIO(response.content)
            
            # 5. Limpieza agresiva de RAM
            del img_64
            del payload
            del response
            gc.collect()
            
            return result

        except requests.exceptions.ConnectionError:
            gc.collect()
            raise Exception("Error de red: La conexión se cerró inesperadamente. Reintenta.")
        except requests.exceptions.HTTPError as e:
            gc.collect()
            if e.response.status_code == 413:
                raise Exception("La imagen es demasiado grande para la versión gratuita.")
            raise Exception(f"Error de la IA: {str(e)}")
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
