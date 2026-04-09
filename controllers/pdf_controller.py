import io
import zipfile
import fitz  # PyMuPDF
from pypdf import PdfWriter, PdfReader

class PDFController:
    """
    Controlador puro para manejar PDFs.
    Sin dependencias de interfaz visual.
    """

    # ─────────────────────────────────────────────────────────────
    # UNIR PDF
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def merge(files_list):
        """
        Recibe una lista ordenada de archivos y los une en uno solo.
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
        Reduce el tamaño del PDF optimizando recursos internos.
        """
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        out = io.BytesIO()
        
        # Guardamos con opciones de compresión real
        doc.save(out, garbage=4, deflate=True, clean=True)
        doc.close()
        
        out.seek(0)
        file.seek(0)
        original_size = len(file.read())
        compressed_size = len(out.getvalue())
        
        return out, original_size, compressed_size

    # ─────────────────────────────────────────────────────────────
    # EXTRAER IMÁGENES (ALTA CALIDAD / NO CORTADAS)
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def extract_images(file):
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            image_count = 0
            for page in doc:
                # 1. Obtener todas las imágenes con sus coordenadas
                items = page.get_image_info(hashes=True)
                if not items: continue

                # 2. Lógica de agrupación: Unimos bboxes que se tocan o están muy cerca
                # Esto evita que las imágenes salgan en "tiras"
                clusters = []
                for item in items:
                    bbox = fitz.Rect(item["bbox"])
                    if bbox.width < 5 or bbox.height < 5: continue # Ignorar ruido
                    
                    added = False
                    for i, cluster in enumerate(clusters):
                        # Si el nuevo bbox toca un cluster existente, lo expandimos
                        if bbox.intersects(cluster) or cluster.distance_to(bbox) < 2:
                            clusters[i] = cluster | bbox
                            added = True
                            break
                    if not added:
                        clusters.append(bbox)

                # 3. Renderizar cada cluster (Imagen completa)
                for i, rect in enumerate(clusters):
                    image_count += 1
                    # Renderizado de alta calidad
                    pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(3, 3))
                    img_data = pix.tobytes("png")
                    zip_file.writestr(f"img_p{page.number+1}_{i+1}.png", img_data)
        
        doc.close()
        zip_buffer.seek(0)
        return zip_buffer, image_count
    # ─────────────────────────────────────────────────────────────
    # EDITOR VISUAL
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def edit(file, pages_config):
        """
        Reordena y rota páginas basándose en una configuración externa.
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
        """Convierte bytes a formato legible (KB, MB)."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
