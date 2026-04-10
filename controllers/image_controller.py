import io
import os
import gc
from huggingface_hub import InferenceClient
from PIL import Image

class ImageController:
    # 🟢 Configuración de IA (Hugging Face)
    # Token tipo 'Write' configurado en las variables de entorno de Render
    HF_TOKEN = os.environ.get("HF_TOKEN")
    
    # Cliente oficial de Hugging Face
    client = InferenceClient(api_key=HF_TOKEN)

    # Modelo de Super-Resolution (Swin2SR) - Excelente balance nitidez/velocidad
    AI_MODEL = "caidas/swin2SR-classical-large-x2"

    @staticmethod
    def upscale_image(file_bytes):
        """
        Punto de entrada principal. 
        Intenta mejorar con IA, si falla, escala con matemáticas.
        """
        gc.collect()
        
        try:
            # 1. Intentamos la mejora con IA (Super-Resolution)
            return ImageController.enhance_image_ai(file_bytes)
        
        except Exception as e:
            # 2. Si la IA falla (503, 401, timeout), usamos el método local
            print(f"IA no disponible, usando respaldo matemático: {e}")
            return ImageController.upscale_pillow_math(file_bytes)

    @staticmethod
    def enhance_image_ai(file_bytes):
        """
        Envía la imagen a Hugging Face para reconstrucción por IA.
        """
        try:
            # Llamada al modelo Swin2SR
            # 'post' envía los bytes crudos y recibe la imagen procesada
            response_data = ImageController.client.post(
                data=file_bytes,
                model=ImageController.AI_MODEL,
                headers={"X-Wait-For-Model": "true"}
            )

            if not response_data or len(response_data) < 100:
                raise Exception("Respuesta de IA inválida")

            result = io.BytesIO(response_data)
            
            # Limpieza inmediata de los bytes de respuesta
            del response_data
            gc.collect()
            
            return result

        except Exception as e:
            # Re-lanzamos el error para que upscale_image use el fallback
            raise e

    @staticmethod
    def upscale_pillow_math(file_bytes, factor=2):
        """
        Escalado tradicional usando interpolación Lanczos (Pillow).
        Es el 'seguro de vida' del sistema.
        """
        gc.collect()
        try:
            img_io = io.BytesIO(file_bytes)
            img = Image.open(img_io)
            
            # Factor de escala (máximo 4 para no explotar la RAM)
            factor = max(1, min(4, factor))
            
            w, h = img.size
            # LANCZOS es el algoritmo matemático más nítido de Pillow
            new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
            
            out = io.BytesIO()
            new_img.save(out, format="PNG")
            out.seek(0)

            # --- LIMPIEZA PROFUNDA ---
            img.close()
            new_img.close()
            del img, new_img, img_io
            gc.collect() 
            
            return out

        except Exception as e:
            gc.collect()
            raise Exception(f"Fallo total en escalado: {str(e)}")
