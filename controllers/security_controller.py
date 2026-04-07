import io
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor

class SecurityController:
    """Controlador puro para encriptación, marcas de agua y numeración."""

    @staticmethod
    def process_watermark(file, text, opacity, color):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 60)
        can.setFillColor(HexColor(color))
        can.setFillAlpha(float(opacity))
        can.saveState()
        can.translate(300, 450)
        can.rotate(45)
        can.drawCentredString(0, 0, text)
        can.restoreState()
        can.save()
        packet.seek(0)

        watermark = PdfReader(packet).pages[0]
        # file.read() si viene de Flask
        reader = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()
        for page in reader.pages:
            page.merge_page(watermark)
            writer.add_page(page)
            
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out

    @staticmethod
    def process_pagination(file, pos):
        reader = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()
        total = len(reader.pages)
        for i in range(total):
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica", 10)
            can.setFillColor(HexColor("#86868b"))
            msg = f"Página {i + 1} de {total}"
            
            if pos == "Abajo Centro":
                can.drawCentredString(300, 30, msg)
            elif pos == "Abajo Derecha":
                can.drawRightString(570, 30, msg)
            else:
                can.drawCentredString(300, 750, msg)
                
            can.save()
            packet.seek(0)
            page = reader.pages[i]
            page.merge_page(PdfReader(packet).pages[0])
            writer.add_page(page)
            
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out

    @staticmethod
    def process_unlock(file, password):
        reader = PdfReader(io.BytesIO(file.read()))
        if reader.is_encrypted:
            result = reader.decrypt(password)
            if result == 0:
                raise ValueError("Contraseña incorrecta. No se pudo desbloquear.")
                
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
            
        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out
