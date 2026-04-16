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
    def merge(files_list, normalize=False):
        """
        Recibe una lista ordenada de archivos y los une en uno solo.
        Si normalize es True, todas las páginas se escalan al tamaño de la primera página.
        """
        merger = PdfWriter()
        target_width = None
        target_height = None

        if normalize and files_list:
            files_list[0].seek(0)
            reference_reader = PdfReader(files_list[0])
            first_page = reference_reader.pages[0]
            target_width = float(first_page.mediabox.width)
            target_height = float(first_page.mediabox.height)
            files_list[0].seek(0)

        for file in files_list:
            reader = PdfReader(file)
            for page in reader.pages:
                if normalize and target_width is not None and target_height is not None:
                    if (float(page.mediabox.width) != target_width or
                            float(page.mediabox.height) != target_height):
                        page.scale_to(target_width, target_height)
                merger.add_page(page)

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

        elif mode == "bookmarks":
            chapters = PDFController._get_bookmark_ranges(reader)
            if not chapters:
                raise ValueError("El PDF no contiene marcadores para dividir por capítulos")

            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                for idx, (title, start, end) in enumerate(chapters, 1):
                    writer = PdfWriter()
                    for i in range(start, end + 1):
                        writer.add_page(reader.pages[i])
                    tmp = io.BytesIO()
                    writer.write(tmp)
                    name = PDFController._sanitize_filename(f"{idx:02d}_{title}.pdf")
                    zf.writestr(name, tmp.getvalue())
            zip_buf.seek(0)
            return zip_buf, "application/zip", "capitulos.zip"

    @staticmethod
    def _get_bookmark_ranges(reader):
        outline = reader.outline
        entries = PDFController._extract_outline_entries(outline, reader)
        if not entries:
            return []

        entries.sort(key=lambda item: item[1])
        chapters = []
        for idx, (title, page_num) in enumerate(entries):
            next_page = entries[idx + 1][1] if idx + 1 < len(entries) else len(reader.pages)
            end_page = next_page - 1
            if page_num <= end_page:
                chapters.append((title, page_num, end_page))
        return chapters

    @staticmethod
    def _extract_outline_entries(outline, reader):
        entries = []
        for item in outline:
            if isinstance(item, list):
                entries.extend(PDFController._extract_outline_entries(item, reader))
            else:
                try:
                    page_num = reader.get_destination_page_number(item)
                except Exception:
                    continue
                title = getattr(item, "title", None) or f"Capítulo {page_num + 1}"
                entries.append((title, page_num))
        return entries

    @staticmethod
    def _sanitize_filename(name):
        cleaned = "".join(
            c if c.isalnum() or c in " ._-()[]" else "_"
            for c in name
        ).strip()
        return cleaned[:100] if cleaned else "capitulo.pdf"

    # ─────────────────────────────────────────────────────────────
    # COMPRIMIR PDF
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def compress(file, level="Media"):
        """
        Reduce el tamaño del PDF optimizando recursos internos.
        Elige una estrategia diferente según si el documento es texto pesado o
        si contiene imágenes grandes que pueden recomprimirse a menor DPI.
        """
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        out = io.BytesIO()

        stats = PDFController._analyze_pdf(doc)
        image_strategy = PDFController._should_optimize_images(stats)

        if image_strategy:
            dpi_target = 72 if level == "Alta" else 150
            quality = 55 if level == "Alta" else (80 if level == "Baja" else 70)
            dpi_threshold = max(2, dpi_target + 1)

            doc.rewrite_images(
                dpi_threshold=dpi_threshold,
                dpi_target=dpi_target,
                quality=quality,
                lossy=True,
                lossless=True,
                bitonal=True,
                color=True,
                gray=True,
            )
            doc.save(out, garbage=4, deflate=True, deflate_images=True, clean=True)
        else:
            doc.save(out, garbage=4, deflate=True, deflate_fonts=True, clean=True)

        doc.close()

        out.seek(0)
        file.seek(0)
        original_size = len(file.read())
        compressed_size = len(out.getvalue())

        return out, original_size, compressed_size

    @staticmethod
    def _analyze_pdf(doc):
        """
        Analiza un PDF y devuelve métricas básicas de texto e imágenes.
        """
        total_text = 0
        total_images = 0
        total_image_pixels = 0
        page_count = len(doc)

        for page in doc:
            total_text += len(page.get_text("text"))
            images = page.get_images(full=True)
            total_images += len(images)
            for img in images:
                if len(img) >= 4:
                    width = img[2]
                    height = img[3]
                else:
                    width = height = 0
                total_image_pixels += width * height

        return {
            "page_count": page_count,
            "total_text": total_text,
            "total_images": total_images,
            "total_image_pixels": total_image_pixels,
            "avg_text_per_page": total_text / page_count if page_count else 0,
            "avg_image_pixels": total_image_pixels / total_images if total_images else 0,
        }

    @staticmethod
    def _should_optimize_images(stats):
        """
        Decide si el PDF debe optimizar principalmente imágenes.
        """
        if stats["total_images"] == 0:
            return False

        if stats["total_image_pixels"] > 3_000_000:
            return True

        if stats["total_images"] >= 3:
            return True

        if stats["avg_image_pixels"] > 300_000:
            return True

        if stats["avg_text_per_page"] < 1500 and stats["total_images"] > 0:
            return True

        return False

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
