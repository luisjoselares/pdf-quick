import io
import zipfile
import fitz
from pypdf import PdfWriter, PdfReader

class PDFController:
    """
    Controlador puro para manejar PDFs.
    Sin dependencias de interfaz visual (Streamlit).
    """

    # ─────────────────────────────────────────────────────────────
    # UNIR PDF
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def merge(files_list):
        """
        Recibe una lista ordenada de archivos (FileStorage de Flask) y los une.
        """
        merger = PdfWriter()
        for file in files_list:
            merger.append(file)
            
        out = io.BytesIO()
        merger.write(out)
        out.seek(0)
        return out

    # ─────────────────────────────────────────────────────────────
    # DIVIDIR PDF
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def split(file, mode="range", start_page=1, end_page=None):
        """
        Extrae páginas de un PDF.
        - mode 'range': Extrae desde start_page hasta end_page.
        - mode 'zip': Genera un ZIP con todas las páginas separadas.
        """
        reader = PdfReader(file)
        total_pages = len(reader.pages)
        
        if mode == "range":
            writer = PdfWriter()
            if end_page is None or end_page > total_pages:
                end_page = total_pages
                
            # Ajuste de índices: el usuario ve páginas del 1 al N, Python del 0 al N-1
            for i in range(start_page - 1, end_page):
                writer.add_page(reader.pages[i])
                
            out = io.BytesIO()
            writer.write(out)
            out.seek(0)
            return out, "application/pdf", "split.pdf"
            
        elif mode == "zip":
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                for i in range(total_pages):
                    w = PdfWriter()
                    w.add_page(reader.pages[i])
                    tmp = io.BytesIO()
                    w.write(tmp)
                    zf.writestr(f"pagina_{i + 1}.pdf", tmp.getvalue())
            zip_buf.seek(0)
            return zip_buf, "application/zip", "paginas_extraidas.zip"

    # ─────────────────────────────────────────────────────────────
    # COMPRIMIR PDF
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def compress(file, level="Media"):
        # Leemos el archivo desde el inicio
        file.seek(0)
        # Abrimos el PDF con PyMuPDF (fitz)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        out = io.BytesIO()
        
        # Guardamos con opciones de compresión real
        # garbage=4: Elimina objetos no usados y compacta
        # deflate=True: Comprime los flujos de datos
        doc.save(out, garbage=4, deflate=True, clean=True)
        doc.close()
        
        out.seek(0)
        file.seek(0)
        original_size = len(file.read())
        compressed_size = len(out.getvalue())
        
        return out, original_size, compressed_size
 
   @staticmethod
    def extract_images(file):
        import zipfile
        import fitz  # PyMuPDF
        import io

        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            image_count = 0
            
            for page in doc:
                # Obtenemos información de todas las imágenes en la página (incluida su posición)
                image_info = page.get_image_info(hashes=True)
                
                # Para evitar duplicados en PDFs que repiten la misma imagen (como logos)
                seen_images = set()

                for img in image_info:
                    # El 'bbox' es el rectángulo (x0, y0, x1, y1) donde está la imagen visualmente
                    bbox = img["bbox"]
                    
                    # Ignorar imágenes demasiado pequeñas (ruido o iconos minúsculos)
                    if bbox[2] - bbox[0] < 10 or bbox[3] - bbox[1] < 10:
                        continue
                    
                    # Crear una imagen (pixmap) solo de esa zona (clip)
                    # Usamos matrix para aumentar la resolución (zoom 2 = mejor calidad)
                    pix = page.get_pixmap(clip=bbox, matrix=fitz.Matrix(2, 2))
                    
                    image_count += 1
                    image_bytes = pix.tobytes("png")
                    
                    filename = f"imagen_pagina_{page.number + 1}_{image_count}.png"
                    zip_file.writestr(filename, image_bytes)
        
        doc.close()
        zip_buffer.seek(0)
        
        if image_count == 0:
            raise Exception("No se encontraron imágenes en el PDF")
            
        return zip_buffer, image_count
    # ─────────────────────────────────────────────────────────────
    # EDITOR VISUAL (Constructor)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def edit(file, pages_config):
        """
        Recibe un JSON/lista con las páginas a conservar, su orden y su rotación.
        Ejemplo: [{"orig": 2, "rot": 90}, {"orig": 0, "rot": 0}]
        """
        reader = PdfReader(file)
        writer = PdfWriter()
        
        for p in pages_config:
            orig_index = p.get("orig")
            rotation = p.get("rot", 0)
            
            if orig_index < len(reader.pages):
                page = reader.pages[orig_index]
                if rotation != 0:
                    page.rotate(rotation)
                writer.add_page(page)
                
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out

    # ─────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def human_size(size_bytes):
        """Transforma bytes a KB/MB (Conservado tal cual tu código)"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
