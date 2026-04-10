# controllers/image_controller.py
import io
import gc
from PIL import Image

class ImageController:
    # --- Borramos TODO lo de MODELS, HF_TOKEN, requests y remove_background ---
    # Tu servidor de Render ya no consumirá RAM procesando fondos.

    @staticmethod
    def upscale_image(file_bytes, factor=2):
        """
        Escalado HD local (Pillow / Lanczos). No consume API externa.
        Muy útil para agrandar imágenes sin pixelarlas.
        """
        # Limpieza inicial
        gc.collect()
        
        try:
            # Abrimos la imagen
            img_io = io.BytesIO(file_bytes)
            img = Image.open(img_io)
            
            # Aseguramos que el factor sea razonable (máx 4 para proteger RAM)
            factor = max(1, min(4, factor))
            
            w, h = img.size
            # Escalado de alta fidelidad matemática (LANCZOS)
            # Esto suaviza los bordes pero no genera nuevos detalles.
            new_img = img.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
            
            # Guardamos en buffer (convertimos a PNG para mantener transparencia)
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
            raise Exception(f"Error al escalar localmente: {str(e)}")
