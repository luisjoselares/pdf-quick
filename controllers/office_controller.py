import streamlit as st
import subprocess
import tempfile
import os
import io
import zipfile
import pandas as pd
from pdf2docx import Converter
import pdfplumber
from PIL import Image
import fitz
from pptx import Presentation
from pptx.util import Inches
from utils.helpers import show_loader


def run_libreoffice(input_path, output_dir):
    try:
        comando = [
            "libreoffice", "--headless", "--convert-to", "pdf",
            input_path, "--outdir", output_dir
        ]
        subprocess.run(comando, check=True, capture_output=True, timeout=60)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(output_dir, f"{base_name}.pdf")
    except FileNotFoundError:
        st.error("LibreOffice no está instalado. La conversión de documentos Office a PDF no está disponible.")
        return None
    except Exception as e:
        st.error(f"Error en el motor de conversión: {e}")
        return None


def handle_conversion(mode, t):
    if mode == "to_pdf":
        title = f"📥 {t.get('to_pdf', 'Convertir A PDF')}"
        subtitle = "Office, HTML e Imágenes hacia PDF."
        allowed = ["docx", "doc", "odt", "xlsx", "xls", "ods", "pptx", "ppt", "txt", "html", "png", "jpg", "jpeg"]
    else:
        title = f"📤 {t.get('from_pdf', 'Extraer DESDE PDF')}"
        subtitle = "PDF hacia Office, HTML e Imágenes."
        allowed = ["pdf"]

    st.markdown(f"#### {title}")
    st.caption(subtitle)

    file = st.file_uploader(
        t.get("drop", "Sube tu archivo"),
        type=allowed,
        key=f"up_{mode}",
        accept_multiple_files=(mode == "to_pdf")
    )

    if file:
        st.markdown("<br>", unsafe_allow_html=True)

        if mode == "from_pdf":
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"📝 {t.get('p2w', 'Word')}", key="p2w", use_container_width=True):
                    process_pdf_to_word(file, t)
            with c2:
                if st.button(f"📊 {t.get('p2e', 'Excel')}", key="p2e", use_container_width=True):
                    process_pdf_to_excel(file, t)
            with c3:
                if st.button("📽️ PPTX", key="p2p", use_container_width=True):
                    process_pdf_to_pptx(file, t)

            c4, c5, c6 = st.columns(3)
            with c4:
                if st.button("🌐 HTML", key="p2h", use_container_width=True):
                    process_pdf_to_html(file, t)
            with c5:
                if st.button("📄 Texto", key="p2t", use_container_width=True):
                    process_pdf_to_txt(file, t)
            with c6:
                img_fmt = st.selectbox("Formato:", ["JPG", "PNG"], label_visibility="collapsed", key="sel_img")
                if st.button(f"🖼️ {t.get('p2i', 'Imagen')}", key="p2i", use_container_width=True):
                    process_pdf_to_image(file, img_fmt, t)
        else:
            if st.button(
                f"⚡ {t.get('btn_proc', 'Procesar')}",
                key=f"btn_go_{mode}",
                use_container_width=True,
                type="primary"
            ):
                if isinstance(file, list):
                    process_multiple_img_to_pdf(file, t)
                else:
                    process_office_to_pdf(file, t)


def process_pdf_to_pptx(file, t):
    loader = show_loader("Generando presentación PPTX", "📽️")
    try:
        doc = fitz.open(stream=file.getvalue(), filetype="pdf")
        prs = Presentation()
        prs.slide_width = Inches(8.5)
        prs.slide_height = Inches(11)
        for page in doc:
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = io.BytesIO(pix.tobytes("png"))
            slide.shapes.add_picture(img_data, 0, 0, width=prs.slide_width, height=prs.slide_height)
        out = io.BytesIO()
        prs.save(out)
        doc.close()
        loader.empty()
        st.success(t.get("success", "Listo"))
        st.download_button(t.get("download", "Descargar"), out.getvalue(), f"{file.name}.pptx", use_container_width=True)
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def process_pdf_to_html(file, t):
    loader = show_loader("Generando HTML", "🌐")
    try:
        doc = fitz.open(stream=file.getvalue(), filetype="pdf")
        html_out = "<html><body>"
        for page in doc:
            html_out += page.get_text("html")
        html_out += "</body></html>"
        doc.close()
        loader.empty()
        st.success(t.get("success", "Listo"))
        st.download_button(
            t.get("download", "Descargar"),
            html_out,
            f"{file.name}.html",
            "text/html",
            use_container_width=True
        )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def process_pdf_to_txt(file, t):
    loader = show_loader("Extrayendo texto", "📄")
    try:
        doc = fitz.open(stream=file.getvalue(), filetype="pdf")
        text_out = ""
        for page in doc:
            text_out += page.get_text()
        doc.close()
        loader.empty()
        st.success(t.get("success", "Listo"))
        st.download_button(
            t.get("download", "Descargar"),
            text_out,
            f"{file.name}.txt",
            "text/plain",
            use_container_width=True
        )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def process_pdf_to_image(file, ext, t):
    loader = show_loader(f"Convirtiendo a {ext}", "🖼️")
    try:
        doc = fitz.open(stream=file.getvalue(), filetype="pdf")
        zip_buffer = io.BytesIO()
        fmt = "jpeg" if ext.upper() == "JPG" else "png"
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                zf.writestr(f"pagina_{i + 1}.{ext.lower()}", pix.tobytes(fmt))
        doc.close()
        loader.empty()
        st.success(t.get("success", "Listo"))
        st.download_button(
            t.get("download", "Descargar") + " (ZIP)",
            zip_buffer.getvalue(),
            f"imagenes_{file.name}.zip",
            use_container_width=True
        )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def process_pdf_to_word(file, t):
    loader = show_loader("Convirtiendo a Word", "📝")
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_p = os.path.join(tmp_dir, "in.pdf")
        docx_p = os.path.join(tmp_dir, "out.docx")
        with open(pdf_p, "wb") as f:
            f.write(file.getvalue())
        try:
            cv = Converter(pdf_p)
            cv.convert(docx_p)
            cv.close()
            loader.empty()
            st.success(t.get("success", "Listo"))
            with open(docx_p, "rb") as f:
                st.download_button(
                    t.get("download", "Descargar"),
                    f.read(),
                    f"{file.name}.docx",
                    use_container_width=True
                )
        except Exception as e:
            loader.empty()
            st.error(f"Error: {e}")


def process_pdf_to_excel(file, t):
    loader = show_loader("Extrayendo tablas a Excel", "📊")
    try:
        tables = []
        with pdfplumber.open(io.BytesIO(file.getvalue())) as pdf:
            for page in pdf.pages:
                tbl = page.extract_table()
                if tbl and len(tbl) > 1:
                    headers = tbl[0]
                    headers = [h if h else f"Col_{i}" for i, h in enumerate(headers)]
                    tables.append(pd.DataFrame(tbl[1:], columns=headers))
        loader.empty()
        if tables:
            out = io.BytesIO()
            pd.concat(tables, ignore_index=True).to_excel(out, index=False, engine='openpyxl')
            st.success(t.get("success", "Listo"))
            st.download_button(
                t.get("download", "Descargar"),
                out.getvalue(),
                f"{file.name}.xlsx",
                use_container_width=True
            )
        else:
            st.warning("No se encontraron tablas estructuradas en el PDF.")
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def process_office_to_pdf(file, t):
    loader = show_loader("Convirtiendo a PDF", "⚡")
    with tempfile.TemporaryDirectory() as tmp_dir:
        in_p = os.path.join(tmp_dir, file.name)
        with open(in_p, "wb") as f:
            f.write(file.getvalue())
        pdf_p = run_libreoffice(in_p, tmp_dir)
        loader.empty()
        if pdf_p and os.path.exists(pdf_p):
            st.success(t.get("success", "Listo"))
            with open(pdf_p, "rb") as f:
                st.download_button(
                    t.get("download", "Descargar"),
                    f.read(),
                    f"{file.name}.pdf",
                    use_container_width=True
                )


def process_multiple_img_to_pdf(files, t):
    loader = show_loader("Uniendo imágenes en PDF", "🖼️")
    try:
        imgs = [Image.open(io.BytesIO(f.getvalue())).convert('RGB') for f in files]
        out = io.BytesIO()
        imgs[0].save(out, format="PDF", save_all=True, append_images=imgs[1:])
        loader.empty()
        st.success(t.get("success", "Listo"))
        st.download_button(
            t.get("download", "Descargar"),
            out.getvalue(),
            "imagenes_unidas.pdf",
            use_container_width=True
        )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")
