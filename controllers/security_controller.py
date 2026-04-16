import io
from pypdf import PdfWriter, PdfReader
from pypdf.constants import UserAccessPermissions
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor

class SecurityController:
    """Controlador puro para encriptación, marcas de agua y numeración."""

    @staticmethod
    def process_watermark(file, text, opacity, color, angle=45, behind=False):
        reader = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()

        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))
            can.setFont("Helvetica-Bold", 60)
            can.setFillColor(HexColor(color))
            can.setFillAlpha(max(0.0, min(1.0, float(opacity))))
            can.saveState()
            can.translate(width / 2, height / 2)
            can.rotate(float(angle))
            can.drawCentredString(0, 0, text)
            can.restoreState()
            can.save()
            packet.seek(0)

            watermark = PdfReader(packet).pages[0]
            if behind:
                watermark.merge_page(page)
                writer.add_page(watermark)
            else:
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

    @staticmethod
    def process_protect(file, password, disable_print=False, disable_copy=False, read_only=False):
        if not password:
            raise ValueError("Se requiere contraseña para proteger el PDF.")

        reader = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        permissions = UserAccessPermissions.all()
        if disable_print:
            permissions &= ~UserAccessPermissions.PRINT
            permissions &= ~UserAccessPermissions.PRINT_TO_REPRESENTATION
        if disable_copy:
            permissions &= ~UserAccessPermissions.EXTRACT_TEXT_AND_GRAPHICS
            permissions &= ~UserAccessPermissions.EXTRACT
        if read_only:
            permissions &= ~UserAccessPermissions.MODIFY
            permissions &= ~UserAccessPermissions.ADD_OR_MODIFY
            permissions &= ~UserAccessPermissions.FILL_FORM_FIELDS
            permissions &= ~UserAccessPermissions.ASSEMBLE_DOC
            permissions &= ~UserAccessPermissions.EXTRACT_TEXT_AND_GRAPHICS
            permissions &= ~UserAccessPermissions.EXTRACT

        writer.encrypt(user_password=password, owner_password=password, permissions_flag=permissions)

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out
