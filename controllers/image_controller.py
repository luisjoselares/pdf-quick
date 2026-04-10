import io
import os
import requests
import gc
import base64
from PIL import Image

class ImageController:
    # Prioridad de modelos para el sistema de respaldo (Fallback)
    MODELS = [
        "https://api-inference.huggingface.co/models/briaai/RMBG-2.0",
        "https://api-inference.huggingface.co/models/ZhengPeng7/BiRefNet_Lite",
        "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
    ]
    
    # El Token se carga desde las variables de entorno de Render
    HF_TOKEN = os.environ.get("HF_TOKEN")

    @staticmethod
    def remove_background(file_bytes):
        """
        Elimina el fondo usando IA. Incluye limpieza agresiva de RAM.
        """
        # Limpieza preventiva antes de empezar
        gc.collect()
        
        try:
            # 1. Convertimos a Base64 (Transporte estable)
            img_64 = base64.b64encode(file_bytes).decode('utf-8')
        except Exception as e:
            gc.collect()
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

        # 2. Bucle de modelos con limpieza en cada intento
        for model_url in ImageController.MODELS:
            try:
                response = requests.post(
                    model_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=60
                )
                
                if response.status_code == 200:
                    # Si tiene éxito, preparamos el resultado
                    result = io.BytesIO(response.content)
                    
                    # --- LIMPIEZA CRÍTICA ---
                    del img_64
                    del payload
                    del response
                    gc.collect() # Forzamos la liberación de los strings pesados
                    
                    return result

                # Si falla el modelo (503, 410, 404), intentamos el siguiente
                continue 

            except Exception as e:
                last_error = str(e)
                continue 

        # 3. Si nada funcionó, barremos la basura antes de lanzar el error
        if 'img_64' in locals(): del img_64
        gc.collect()
        raise Exception(f"IA no disponible temporalmente: {last_error}")

    @staticmethod
    def upscale_image(file_bytes, factor=2):
        """
        Aumenta el tamaño localmente. Optimizado para no saturar la RAM.
        """
        # Limpieza inicial
        gc.collect()
        
        try:
            # Abrimos la imagen
            img_io = io.BytesIO(file_bytes)
            img = Image.open(img_io)
            
            w, h = img.size
            # Escalado de alta calidad (LANCZOS)
            new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
            
            # Guardamos en buffer
            out = io.BytesIO()
            new_img.save(out, format="PNG")
            out.seek(0)

            # --- LIMPIEZA DE OBJETOS PILLOW ---
            img.close()
            new_img.close()
            del img, new_img, img_io
            
            # Escoba final
            gc.collect() 
            
            return out

        except Exception as e:
            gc.collect()
            raise Exception(f"Error al escalar: {str(e)}")
