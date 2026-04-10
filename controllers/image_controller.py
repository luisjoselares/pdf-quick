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

    @staticmethod
    def remove_background(file_bytes):
        """
        Intenta eliminar el fondo usando una lista de modelos. 
        Si uno falla o da 410, pasa al siguiente automáticamente.
        """
        # 1. Convertimos a Base64 para un transporte de datos más estable (estilo Groq)
        try:
            img_64 = base64.b64encode(file_bytes).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error al codificar imagen: {str(e)}")

        payload = {
            "inputs": img_64,
            "parameters": {"wait_for_model": True}
        }
        
        headers = {
            "Authorization": f"Bearer {ImageController.HF_TOKEN}",
            "Content-Type": "application/json",
            "Connection": "close" 
        }

        last_error = "No se pudo conectar con ningún motor de IA."

        # 2. Bucle de reintentos con diferentes modelos
        for model_url in ImageController.MODELS:
            try:
                response = requests.post(
                    model_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=60
                )
                
                # Si el modelo está cargando (503), esperamos un poco o pasamos al siguiente
                if response.status_code == 503:
                    continue 

                # Si el modelo ya no existe (410/404), pasamos al siguiente
                if response.status_code in [404, 410]:
                    continue

                response.raise_for_status()
                
                # Verificamos integridad
                if not response.content or len(response.content) < 100:
                    continue

                # Si llegamos aquí, tuvimos éxito
                result = io.BytesIO(response.content)
                
                # Limpieza de seguridad
                del img_64
                del payload
                gc.collect()
                
                return result

            except Exception as e:
                last_error = str(e)
                continue # Probar el siguiente modelo en la lista

        # 3. Si sale del bucle sin retornar, nada funcionó
        gc.collect()
        raise Exception(f"IA no disponible: {last_error}. Intenta con una imagen más pequeña.")

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
