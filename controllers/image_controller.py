import io
import os
import gc
from huggingface_hub import InferenceClient
from PIL import Image

class ImageController:
    # Inicializamos el cliente. 
    # El api_key se toma de tu variable HF_TOKEN en Render.
    client = InferenceClient(api_key=os.environ.get("HF_TOKEN"))

    @staticmethod
    def remove_background(file_bytes):
        """
        Elimina el fondo usando el InferenceClient con el proveedor fal-ai.
        """
        # Limpieza preventiva
        gc.collect()
        
        try:
            # 1. Convertimos los bytes a un objeto que el cliente pueda leer
            input_image = io.BytesIO(file_bytes)
            
            # 2. Llamada a la API usando el motor de fal-ai (Súper rápido)
            # Nota: Si fal-ai da problemas de región, quitamos 'provider' y usará el default
            output_image = ImageController.client.image_segmentation(
                input_image,
                model="briaai/RMBG-2.0",
                provider="fal-ai"
            )
            
            # 3. El output de 'image_segmentation' es una imagen PIL directamente
            img_io = io.BytesIO()
            output_image.save(img_io, format="PNG")
            img_io.seek(0)
            
            # --- BORRADO DE BASURA CRÍTICO ---
            input_image.close()
            output_image.close()
            del input_image
            del output_image
            gc.collect() 
            
            return img_io

        except Exception as e:
            gc.collect()
            # Si fal-ai falla por créditos o región, lanzamos un mensaje claro
            error_msg = str(e)
            if "provider" in error_msg.lower():
                raise Exception("El motor fal-ai no está disponible. Reintentando sin proveedor...")
            raise Exception(f"Error de IA: {error_msg}")

    @staticmethod
    def upscale_image(file_bytes, factor=2):
        # (Tu código de escalado local se queda igual, ya que funciona de toque)
        try:
            img = Image.open(io.BytesIO(file_bytes))
            w, h = img.size
            new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            new_img.save(out, format="PNG")
            out.seek(0)
            img.close()
            del img, new_img
            gc.collect()
            return out
        except Exception as e:
            gc.collect()
            raise Exception(f"Error al escalar: {str(e)}")
