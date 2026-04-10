import io
import os
import requests
import gc
import base64
from PIL import Image

class ImageController:
    # Lista de modelos en orden de prioridad (Los más estables en 2026)
    MODELS = [
        "https://api-inference.huggingface.co/models/briaai/RMBG-2.0",
        "https://api-inference.huggingface.co/models/ZhengPeng7/BiRefNet_Lite",
        "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
    ]
    
    HF_TOKEN = os.environ.get("HF_TOKEN")

    class ImageController:
    # Prioridad de modelos (El 2.0 es el que aceptaste términos probablemente)
    MODELS = [
        "https://api-inference.huggingface.co/models/briaai/RMBG-2.0",
        "https://api-inference.huggingface.co/models/ZhengPeng7/BiRefNet_Lite",
        "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
    ]
    
    # Se carga desde Render (Asegúrate de poner aquí el Token de 'Write')
    HF_TOKEN = os.environ.get("HF_TOKEN")

    @staticmethod
    def remove_background(file_bytes):
        """
        Elimina el fondo usando IA con transporte Base64 para evitar errores de conexión.
        """
        try:
            # Convertimos la imagen a texto (Base64) para que viaje sin romperse
            img_64 = base64.b64encode(file_bytes).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error al procesar imagen: {str(e)}")

        payload = {
            "inputs": img_64,
            "parameters": {"wait_for_model": True}
        }
        
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "Content-Type": "application/json",
            "Connection": "close" 
        }

        last_error = "No se pudo conectar con los motores de IA."

        # Intentamos con la lista de modelos
        for model_url in ImageController.MODELS:
            try:
                response = requests.post(
                    model_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=60
                )
                
                # Si el modelo está despertando, esperamos o pasamos al siguiente
                if response.status_code == 503:
                    continue 

                # Si el modelo no está disponible en este endpoint, pasamos al siguiente
                if response.status_code in [404, 410]:
                    continue

                response.raise_for_status()
                
                # Verificación de que recibimos una imagen válida
                if not response.content or len(response.content) < 100:
                    continue

                # Éxito: Devolvemos el buffer de la imagen
                result = io.BytesIO(response.content)
                
                # Limpieza de RAM antes de retornar
                del img_64
                del payload
                gc.collect()
                
                return result

            except Exception as e:
                last_error = str(e)
                continue 

        # Si llegamos aquí, nada funcionó
        gc.collect()
        raise Exception(f"IA no disponible temporalmente: {last_error}")

    @staticmethod
    def upscale_image(file_bytes, factor=2):
        """
        Aumenta el tamaño de la imagen localmente usando Pillow (LANCZOS).
        """
        try:
            img = Image.open(io.BytesIO(file_bytes))
            w, h = img.size
            
            # Escalado de alta fidelidad
            new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
            
            out = io.BytesIO()
            new_img.save(out, format="PNG")
            out.seek(0)

            # --- Limpieza de memoria crítica para Render ---
            img.close()
            del img
            del new_img
            gc.collect() 
            
            return out

        except Exception as e:
            gc.collect()
            raise Exception(f"Error al escalar: {str(e)}")
