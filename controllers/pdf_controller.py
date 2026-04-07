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
        """
        Reduce la calidad de las imágenes internas del PDF.
        Retorna el buffer, el tamaño original y el tamaño comprimido.
        """
        dpi_map = {"Baja": 72, "Media": 96, "Alta": 150}
        quality_map = {"Baja": 55, "Media": 72, "Alta": 88}
        
        dpi = dpi_map.get(level, 96)
        quality = quality_map.get(level, 72)
        
        file_bytes = file.read()
        original_size = len(file_bytes)
        
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        out = io.BytesIO()
        zoom = dpi / 72
        new_doc = fitz.open()
        
        for page in doc:
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            img_page.insert_image(
                img_page.rect,
                stream=pix.tobytes("jpeg", jpg_quality=quality)
            )
            
        new_doc.save(out, garbage=4, deflate=True, clean=True)
        doc.close()
        new_doc.close()
        out.seek(0)
        
        compressed_size = len(out.getvalue())
        return out, original_size, compressed_size

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
