import streamlit as st
from pypdf import PdfWriter, PdfReader
import io
import fitz
import zipfile
from utils.helpers import show_loader

# ─────────────────────────────────────────────────────────────
# CALLBACKS DE ESTADO (Previenen bloqueos e infinitos loops)
# ─────────────────────────────────────────────────────────────
def move_merge_up(idx):
    if idx > 0:
        st.session_state.merge_order[idx], st.session_state.merge_order[idx-1] = st.session_state.merge_order[idx-1], st.session_state.merge_order[idx]

def move_merge_down(idx):
    if idx < len(st.session_state.merge_order) - 1:
        st.session_state.merge_order[idx], st.session_state.merge_order[idx+1] = st.session_state.merge_order[idx+1], st.session_state.merge_order[idx]

def remove_merge_file(idx):
    st.session_state.merge_order.pop(idx)

def rot_page(idx):
    st.session_state.edit_pages[idx]["rot"] = (st.session_state.edit_pages[idx]["rot"] - 90) % 360

def del_page(idx):
    st.session_state.edit_pages.pop(idx)


# ─────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────
def render_pdf_seo_content(tool, t):
    """Contenido SEO/instrucciones cuando no hay archivo cargado."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"**{t.get('how_to', 'Cómo usar')}**")
    st.write(f"1. {t.get('step_1', 'Sube tu archivo')}")
    st.write(f"2. {t.get('step_2', 'Ajusta las opciones')}")
    st.write(f"3. {t.get('step_3', 'Descarga el resultado')}")
    st.caption(f"🔒 {t.get('privacy_note', 'Procesado en memoria.')}")

def render_pdf_preview(file, page_numbers, rotations=None):
    try:
        doc = fitz.open(stream=file.getvalue(), filetype="pdf")
        with st.container(height=400, border=True):
            cols_per_row = 3
            for i in range(0, len(page_numbers), cols_per_row):
                cols = st.columns(cols_per_row)
                chunk = page_numbers[i: i + cols_per_row]
                for idx, p_num in enumerate(chunk):
                    page = doc.load_page(p_num - 1)
                    m = fitz.Matrix(0.2, 0.2)
                    if rotations and str(p_num) in rotations:
                        m = m.prerotate(rotations[str(p_num)])
                    pix = page.get_pixmap(matrix=m)
                    with cols[idx]:
                        st.image(pix.tobytes("png"), use_container_width=True)
                        st.caption(f"Pág. {p_num}")
        doc.close()
    except Exception as e:
        st.error(f"Error en vista previa: {e}")


# ─────────────────────────────────────────────────────────────
# UNIR PDF
# ─────────────────────────────────────────────────────────────
def handle_merge(t):
    st.markdown(f"### 🗂️ {t.get('m_merge', 'Unir PDF')}")
    st.markdown(
        f"<p class='tool-description'>{t.get('desc_merge', 'Sube los PDFs y ordénalos visualmente.')}</p>",
        unsafe_allow_html=True
    )

    files = st.file_uploader(
        t.get("drop", "Arrastra tu archivo aquí"),
        type="pdf",
        accept_multiple_files=True,
        key="up_merge"
    )

    if not files:
        render_pdf_seo_content("merge", t)
    else:
        # Inicializar o actualizar el orden en el estado de sesión
        current_filenames = [f.name for f in files]
        if "merge_order" not in st.session_state or st.session_state.get("last_merge_files") != current_filenames:
            st.session_state.merge_order = current_filenames.copy()
            st.session_state.last_merge_files = current_filenames.copy()

        file_dict = {f.name: f for f in files}

        st.write("**Orden visual (Mueve o elimina archivos):**")
        
        # Grid visual interactivo en lugar del multiselect
        with st.container(border=True):
            for idx, fname in enumerate(st.session_state.merge_order):
                col_img, col_name, col_btns = st.columns([1, 4, 2], gap="small")
                
                with col_img:
                    try:
                        f = file_dict[fname]
                        doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                        page = doc.load_page(0)
                        pix = page.get_pixmap(matrix=fitz.Matrix(0.1, 0.1))
                        st.image(pix.tobytes("png"), width=40)
                        doc.close()
                    except:
                        st.write("📄")
                
                with col_name:
                    st.write(f"**{idx + 1}.** {fname}")
                
                with col_btns:
                    b1, b2, b3 = st.columns(3)
                    b1.button("⬆️", key=f"up_{idx}_{fname}", on_click=move_merge_up, args=(idx,), disabled=(idx == 0))
                    b2.button("⬇️", key=f"dw_{idx}_{fname}", on_click=move_merge_down, args=(idx,), disabled=(idx == len(st.session_state.merge_order)-1))
                    b3.button("✕", key=f"rm_{idx}_{fname}", on_click=remove_merge_file, args=(idx,))

        if len(st.session_state.merge_order) > 0:
            if st.button(t.get("btn_proc", "Procesar"), key="do_merge", type="primary", use_container_width=True):
                loader = show_loader("Uniendo archivos")
                try:
                    merger = PdfWriter()
                    for name in st.session_state.merge_order:
                        merger.append(file_dict[name])
                    out = io.BytesIO()
                    merger.write(out)
                    loader.empty()
                    st.success(f"✅ {t.get('success', 'Listo')} — {len(st.session_state.merge_order)} archivos combinados")
                    st.download_button(
                        t.get("download", "Descargar"),
                        out.getvalue(),
                        "merged.pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    loader.empty()
                    st.error(f"Error: {e}")
        else:
            st.warning("No hay archivos en la lista para unir.")


# ─────────────────────────────────────────────────────────────
# DIVIDIR PDF
# ─────────────────────────────────────────────────────────────
def handle_split(t):
    st.markdown(f"### ✂️ {t.get('m_split', 'Dividir PDF')}")
    st.markdown(
        f"<p class='tool-description'>{t.get('desc_split', 'Elige las páginas a extraer.')}</p>",
        unsafe_allow_html=True
    )

    file = st.file_uploader(
        t.get("drop", "Arrastra tu archivo aquí"),
        type="pdf",
        key="up_split"
    )

    if not file:
        render_pdf_seo_content("split", t)
    else:
        reader = PdfReader(file)
        total = len(reader.pages)
        c1, c2 = st.columns([1, 1.5], gap="large")

        with c1:
            mode = st.selectbox("Modo:", ["Rango de páginas", "Todas las páginas (ZIP)"])
            rng = (1, total)
            if mode == "Rango de páginas":
                rng = st.slider("Páginas:", 1, total, (1, total))
                pages_to_show = list(range(rng[0], rng[1] + 1))
            else:
                pages_to_show = list(range(1, total + 1))

            st.caption(f"Documento: {total} páginas")

            if st.button(t.get("btn_proc", "Procesar"), key="do_split", type="primary", use_container_width=True):
                execute_split_logic(file, mode, rng, t)

        with c2:
            st.caption("Vista previa")
            render_pdf_preview(file, pages_to_show)


# ─────────────────────────────────────────────────────────────
# COMPRIMIR PDF
# ─────────────────────────────────────────────────────────────
def handle_compress(t):
    st.markdown(f"### 🗜️ {t.get('m_comp', 'Comprimir')}")
    st.markdown(
        f"<p class='tool-description'>{t.get('desc_compress', 'Reduce el tamaño del archivo.')}</p>",
        unsafe_allow_html=True
    )

    file = st.file_uploader(
        t.get("drop", "Arrastra tu archivo aquí"),
        type="pdf",
        key="up_comp"
    )

    if not file:
        render_pdf_seo_content("compress", t)
    else:
        level = st.select_slider(
            "Calidad de imagen:",
            options=["Baja", "Media", "Alta"],
            value="Media"
        )
        dpi_map = {"Baja": 72, "Media": 96, "Alta": 150}
        quality_map = {"Baja": 55, "Media": 72, "Alta": 88}
        dpi = dpi_map[level]
        quality = quality_map[level]

        if st.button(t.get("btn_proc", "Procesar"), key="do_comp", type="primary", use_container_width=True):
            loader = show_loader("Comprimiendo", "🗜️")
            try:
                doc = fitz.open(stream=file.getvalue(), filetype="pdf")
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
                original_size = len(file.getvalue())
                compressed_size = len(out.getvalue())
                reduction = round((1 - compressed_size / original_size) * 100, 1)
                loader.empty()
                if reduction > 0:
                    st.success(f"✅ Reducción del **{reduction}%** — de {_human_size(original_size)} a {_human_size(compressed_size)}")
                else:
                    st.info("El archivo ya estaba optimizado al máximo.")
                st.download_button(
                    t.get("download", "Descargar"),
                    out.getvalue(),
                    f"min_{file.name}",
                    use_container_width=True
                )
            except Exception as e:
                loader.empty()
                st.error(f"Error: {e}")


# ─────────────────────────────────────────────────────────────
# EDITOR VISUAL
# ─────────────────────────────────────────────────────────────
def handle_editor(t):
    st.markdown(f"### 🔄 {t.get('m_editor', 'Editor Visual')}")
    st.markdown(
        f"<p class='tool-description'>{t.get('desc_editor', 'Rota, elimina o reordena páginas visualmente.')}</p>",
        unsafe_allow_html=True
    )

    file = st.file_uploader(
        t.get("drop", "Arrastra tu archivo aquí"),
        type="pdf",
        key="up_edit"
    )

    if not file:
        render_pdf_seo_content("editor", t)
    else:
        if "edit_pages" not in st.session_state or st.session_state.get("last_file") != file.name:
            reader = PdfReader(file)
            st.session_state.edit_pages = [{"orig": i, "rot": 0} for i in range(len(reader.pages))]
            st.session_state.last_file = file.name

        c1, c2 = st.columns([1, 2.5], gap="medium")
        with c1:
            st.write("**Herramientas**")
            if st.button("Reiniciar orden", use_container_width=True):
                del st.session_state.edit_pages
                st.rerun()
            if st.button(
                t.get("btn_proc", "Guardar PDF"),
                key="save_edit",
                type="primary",
                use_container_width=True
            ):
                execute_editor_save(file, t)
            st.caption(f"{len(st.session_state.edit_pages)} páginas")

        with c2:
            st.write("**Mesa de trabajo**")
            pages = st.session_state.edit_pages
            doc = fitz.open(stream=file.getvalue(), filetype="pdf")
            
            # FIX: Renderizado robusto. Se usan contenedores de altura fija para que la UI no salte al cambiar proporciones.
            for i in range(0, len(pages), 3):
                cols = st.columns(3)
                for idx, page_data in enumerate(pages[i:i + 3]):
                    actual_idx = i + idx
                    with cols[idx]:
                        # El contenedor fijo es la clave: bloquea la altura
                        with st.container(height=320, border=True):
                            p_obj = doc.load_page(page_data["orig"])
                            pix = p_obj.get_pixmap(
                                matrix=fitz.Matrix(0.2, 0.2).prerotate(page_data["rot"])
                            )
                            # Se restringe el alto máximo de la imagen para que encaje
                            st.image(pix.tobytes("png"), use_container_width=True)
                            
                            st.caption(f"Pág. {actual_idx + 1}")
                            
                            b1, b2 = st.columns(2)
                            b1.button("↩", key=f"r_{actual_idx}_{page_data['orig']}", on_click=rot_page, args=(actual_idx,), help="Rotar 90°")
                            b2.button("✕", key=f"d_{actual_idx}_{page_data['orig']}", on_click=del_page, args=(actual_idx,), help="Eliminar página")
            doc.close()


# ─────────────────────────────────────────────────────────────
# LÓGICAS INTERNAS
# ─────────────────────────────────────────────────────────────
def execute_split_logic(file, mode, rng, t):
    loader = show_loader("Dividiendo", "✂️")
    try:
        reader = PdfReader(file)
        if "Rango" in mode:
            writer = PdfWriter()
            for i in range(rng[0] - 1, rng[1]):
                writer.add_page(reader.pages[i])
            out = io.BytesIO()
            writer.write(out)
            loader.empty()
            st.success(f"✅ Páginas {rng[0]}–{rng[1]} extraídas")
            st.download_button(
                t.get("download", "Descargar"),
                out.getvalue(),
                "split.pdf",
                use_container_width=True
            )
        else:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                for i in range(len(reader.pages)):
                    w = PdfWriter()
                    w.add_page(reader.pages[i])
                    tmp = io.BytesIO()
                    w.write(tmp)
                    zf.writestr(f"pagina_{i + 1}.pdf", tmp.getvalue())
            loader.empty()
            st.success(f"✅ ZIP con {len(reader.pages)} páginas generado")
            st.download_button(
                "Descargar ZIP",
                zip_buf.getvalue(),
                "paginas.zip",
                use_container_width=True
            )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def execute_editor_save(file, t):
    loader = show_loader("Construyendo PDF", "🔄")
    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        for p in st.session_state.edit_pages:
            page = reader.pages[p["orig"]]
            page.rotate(p["rot"])
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        loader.empty()
        st.success("✅ PDF guardado")
        st.download_button(
            t.get("download", "Descargar"),
            out.getvalue(),
            f"edit_{file.name}",
            use_container_width=True
        )
    except Exception as e:
        loader.empty()
        st.error(f"Error: {e}")


def _human_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
