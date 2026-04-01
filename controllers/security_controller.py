import streamlit as st
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
import io
from utils.helpers import show_loader


def handle_security(t):
    st.markdown(f"## {t.get('sec_title', 'Seguridad')}")

    file = st.file_uploader(t.get("drop", "Sube tu PDF"), type="pdf", key="up_security")

    if not file:
        st.info("Sube un PDF para acceder a las herramientas de seguridad.")
    else:
        tab_water, tab_number, tab_unlock = st.tabs(["Marca de Agua", "Numeración", "Desbloquear"])

        with tab_water:
            text = st.text_input("Texto de la marca:", "CONFIDENCIAL")
            col1, col2 = st.columns(2)
            opacity = col1.slider("Opacidad", 0.1, 1.0, 0.3, key="wm_opacity")
            color = col2.color_picker("Color", "#FF0000", key="wm_color")
            if st.button("Aplicar Marca de Agua", use_container_width=True, key="btn_watermark"):
                process_watermark(file, text, opacity, color, t)

        with tab_number:
            pos = st.selectbox("Posición:", ["Abajo Centro", "Abajo Derecha", "Arriba Centro"])
            if st.button("Numerar Páginas", use_container_width=True, key="btn_number"):
                process_pagination(file, pos, t)

        with tab_unlock:
            st.info("Se eliminará la protección contra copia/impresión.")
            password = st.text_input("Contraseña (si aplica):", type="password", key="unlock_pass")
            if st.button("Liberar PDF", use_container_width=True, key="btn_unlock"):
                process_unlock(file, password, t)


def process_watermark(file, text, opacity, color, t):
    loader = show_loader("Estampando marca de agua", "🛡️")
    try:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 60)
        can.setFillColor(HexColor(color))
        can.setFillAlpha(opacity)
        can.saveState()
        can.translate(300, 450)
        can.rotate(45)
        can.drawCentredString(0, 0, text)
        can.restoreState()
        can.save()
        packet.seek(0)

        watermark = PdfReader(packet).pages[0]
        reader = PdfReader(io.BytesIO(file.getvalue()))
        writer = PdfWriter()
        for page in reader.pages:
            page.merge_page(watermark)
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        loader.empty()
        st.success(t.get("success", "Listo"))
        st.download_button(
            t.get("download", "Descargar"),
            out.getvalue(),
            f"marked_{file.name}",
            use_container_width=True
        )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def process_pagination(file, pos, t):
    loader = show_loader("Numerando páginas", "🔢")
    try:
        reader = PdfReader(io.BytesIO(file.getvalue()))
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
        loader.empty()
        st.success(t.get("success", "Listo"))
        st.download_button(
            t.get("download", "Descargar"),
            out.getvalue(),
            f"num_{file.name}",
            use_container_width=True
        )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def process_unlock(file, password, t):
    loader = show_loader("Desbloqueando PDF", "🔓")
    try:
        reader = PdfReader(io.BytesIO(file.getvalue()))
        if reader.is_encrypted:
            result = reader.decrypt(password)
            if result == 0:
                loader.empty()
                st.error("Contraseña incorrecta. No se pudo desbloquear el PDF.")
                return
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        loader.empty()
        st.success("Documento desbloqueado.")
        st.download_button(
            t.get("download", "Descargar"),
            out.getvalue(),
            f"unlocked_{file.name}",
            use_container_width=True
        )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")
