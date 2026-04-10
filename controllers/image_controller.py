import io
import gc
import zipfile
import fitz

class ImageController:
    @staticmethod
    def extract_images_from_pdf(file):
        """
        Extrae todas las imágenes embebidas de un PDF y retorna un ZIP en memoria.
        """
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            image_count = 0
            for page in doc:
                for idx, img in enumerate(page.get_images(full=True), start=1):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n > 3:
                        rgb = fitz.Pixmap(fitz.csRGB, pix)
                        pix.close()
                        pix = rgb

                    img_data = pix.tobytes("png")
                    zip_file.writestr(f"pagina_{page.number + 1}_img_{idx}.png", img_data)
                    pix.close()
                    image_count += 1

        doc.close()
        zip_buffer.seek(0)
        gc.collect()
        return zip_buffer, image_count
