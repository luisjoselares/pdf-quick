import streamlit as st
import fitz
import os
import io
import re
from datetime import date
from huggingface_hub import InferenceClient
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from utils.helpers import show_loader

HF_TOKEN = os.getenv("HF_Token")

MODELS = {
    "summarize": "facebook/bart-large-cnn",
    "analyze":   "Qwen/Qwen2.5-7B-Instruct",  # Cambiado por estabilidad en la API gratuita
    "translate": "Helsinki-NLP/opus-mt-es-en",
}


# ─────────────────────────────────────────────────────────────
# INTERFAZ
# ─────────────────────────────────────────────────────────────
def handle_ai_tools(t):
    st.markdown(f"## {t.get('ai_asst', 'Asistente IA')}")

    if not HF_TOKEN:
        st.warning(
            "Para usar el Asistente IA configura el Secret **HF_Token** "
            "con tu token de HuggingFace."
        )
        return

    file = st.file_uploader(
        t.get("drop", "Sube un PDF"), type="pdf", key="up_ai_tool"
    )

    if not file:
        st.info("Sube un PDF para analizarlo con IA. Se generará un PDF descargable con el resultado.")
        return

    # Leer el PDF para saber cuántas páginas tiene
    try:
        doc_info = fitz.open(stream=file.getvalue(), filetype="pdf")
        total_pages = len(doc_info)
        doc_info.close()
    except Exception:
        st.error("Error al leer el PDF. Asegúrate de que no esté corrupto o protegido con contraseña.")
        return

    st.markdown("---")
    col_opt, col_res = st.columns([1, 1.5], gap="large")

    with col_opt:
        st.write("### Configuración")
        action = st.radio(
            "Acción:",
            ["Resumen Ejecutivo", "Extraer Puntos Clave", "Traducción (ES → EN)"],
            key="ai_action",
        )

        st.write(f"**Documento de {total_pages} páginas.**")
        
        # FIX: Selector específico de páginas con límites estrictos
        max_allowed = 5
        st.caption(f"⚠️ Por limitaciones del servidor, puedes seleccionar **máximo {max_allowed} páginas**.")
        
        all_pages_list = [i for i in range(1, total_pages + 1)]
        default_selection = all_pages_list[:min(3, total_pages)] # Por defecto selecciona las primeras 3 (o menos)
        
        selected_pages = st.multiselect(
            "Selecciona las páginas a procesar:",
            options=all_pages_list,
            default=default_selection,
            max_selections=max_allowed,
            help="Elige páginas específicas (ej. 1, 3, 5)."
        )

        if not selected_pages:
            st.warning("Debes seleccionar al menos una página.")
        else:
            if st.button("Procesar con IA", use_container_width=True, type="primary", key="btn_ai"):
                _run_ai(file, action, selected_pages, t)

    with col_res:
        st.write("### Resultado")

        if "ai_pdf" in st.session_state:
            st.success("Análisis completado — PDF listo")

            _action_file = {
                "Resumen Ejecutivo":       "resumen",
                "Extraer Puntos Clave":    "puntos_clave",
                "Traducción (ES → EN)":    "traduccion",
            }
            slug = _action_file.get(st.session_state.get("ai_action_done", ""), "analisis")
            fname = f"{slug}_{file.name}"

            st.download_button(
                "⬇️  Descargar PDF",
                data=st.session_state.ai_pdf,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="dl_ai_pdf",
            )

            if "ai_preview" in st.session_state:
                with st.expander("Vista previa del texto", expanded=False):
                    st.write(st.session_state.ai_preview)

            if st.button("Limpiar resultado", use_container_width=True, key="btn_clear_ai"):
                for k in ("ai_pdf", "ai_preview", "ai_action_done"):
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            st.caption("El PDF con el resultado aparecerá aquí una vez procesado.")


# ─────────────────────────────────────────────────────────────
# ORQUESTADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────
def _run_ai(file, action, selected_pages, t):
    loader = show_loader("La IA está analizando el documento", "🧠")
    try:
        # ── Extraer texto SOLO de las páginas seleccionadas ──
        doc = fitz.open(stream=file.getvalue(), filetype="pdf")
        pages_text = []
        
        # selected_pages son números del 1 a N. Fitz usa índices de 0 a N-1.
        for p_num in sorted(selected_pages):
            idx = p_num - 1
            if 0 <= idx < len(doc):
                text = doc[idx].get_text()
                if text.strip():
                    pages_text.append(text)
        doc.close()

        if not pages_text:
            loader.empty()
            st.error("No se detectó texto legible en las páginas seleccionadas (podrían ser imágenes).")
            return

        pages_str = ", ".join(map(str, sorted(selected_pages)))

        # ── Acción ────────────────────────────────────────────
        if action == "Resumen Ejecutivo":
            combined_text = "\n".join(pages_text)
            result_text = _summarize(combined_text)
            title       = "Resumen Ejecutivo"
            subtitle    = f"Análisis de la(s) página(s): {pages_str}"

        elif action == "Extraer Puntos Clave":
            combined_text = "\n".join(pages_text)
            result_text = _key_points(combined_text)
            title       = "Puntos Clave del Documento"
            subtitle    = f"Extraído de la(s) página(s): {pages_str}"

        else:  # Traducción
            result_text = _translate_pages(pages_text)
            title       = "Documento Traducido  (ES → EN)"
            subtitle    = f"Translated page(s): {pages_str} · PDF QUICK AI"

        # ── Generar PDF ───────────────────────────────────────
        pdf_bytes = _build_pdf(title, subtitle, result_text, file.name)

        st.session_state.ai_pdf         = pdf_bytes
        st.session_state.ai_preview     = result_text[:600] + ("…" if len(result_text) > 600 else "")
        st.session_state.ai_action_done = action

        loader.empty()
        st.rerun()

    except Exception as e:
        loader.empty()
        err = str(e)
        if "429" in err:
            st.warning("Los servidores de IA están saturados. Reintenta en 20 segundos.")
        elif "token" in err.lower() or "auth" in err.lower() or "unauthorized" in err.lower():
            st.error("Error de autenticación: verifica que **HF_Token** sea correcto.")
        else:
            st.error(f"Error técnico: {e}")


# ─────────────────────────────────────────────────────────────
# MOTORES IA
# ─────────────────────────────────────────────────────────────

def _clean(text: str, max_chars: int = 15000) -> str:
    """Limpia y trunca texto. Límite alto, el manejo real se hace en cada motor."""
    text = re.sub(r"[^\w\s.,;:!?()\'\"\-\náéíóúüñÁÉÍÓÚÜÑ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

def _summarize(text: str) -> str:
    """Resumen ejecutivo con BART — procesado en trozos seguros para evitar 'index out of range'."""
    clean_text = _clean(text, max_chars=15000)
    client = InferenceClient(MODELS["summarize"], token=HF_TOKEN)
    
    # BART soporta máximo 1024 tokens. Partimos en bloques de 1800 caracteres (~450 tokens) para estar súper seguros.
    chunks, remaining = [], clean_text
    while remaining:
        if len(remaining) <= 1800:
            chunks.append(remaining)
            break
        cut = remaining[:1800].rfind(" ")
        cut = cut if cut > 0 else 1800
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    summarized_chunks = []
    for chunk in chunks:
        if len(chunk) < 100:
            continue
        try:
            resp = client.summarization(chunk)
            # Manejo ultra-seguro de la respuesta
            if isinstance(resp, str):
                summarized_chunks.append(resp)
            elif hasattr(resp, "summary_text"):
                summarized_chunks.append(resp.summary_text)
            elif isinstance(resp, list) and len(resp) > 0 and isinstance(resp[0], dict):
                summarized_chunks.append(resp[0].get("summary_text", str(resp)))
            elif isinstance(resp, dict):
                summarized_chunks.append(resp.get("summary_text", str(resp)))
            else:
                summarized_chunks.append(str(resp))
        except Exception:
            # Si un fragmento falla, ignoramos ese pedacito y continuamos con el resto del documento
            continue

    return "\n\n".join(summarized_chunks) if summarized_chunks else "No se pudo generar el resumen por saturación de la API."


def _key_points(text: str) -> str:
    """Extrae 5 puntos clave usando Qwen vía chat_completion (ultra estable)."""
    clean = _clean(text, max_chars=8000)
    client = InferenceClient(token=HF_TOKEN)
    
    try:
        response = client.chat_completion(
            model=MODELS["analyze"],
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente experto en análisis de documentos."
                },
                {
                    "role": "user",
                    "content": (
                        "Extrae exactamente 5 puntos clave del siguiente texto. "
                        "Cada punto debe comenzar con '• ' en una nueva línea. "
                        "Sé conciso y responde en el mismo idioma del texto original.\n\nTexto:\n" + clean
                    ),
                }
            ],
            max_tokens=450,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error al generar puntos clave: {str(e)}"


def _translate_pages(pages_text: list) -> str:
    """Traduce la lista de textos (páginas) en trozos de ≤800 chars."""
    client = InferenceClient(MODELS["translate"], token=HF_TOKEN)
    translated_pages = []

    for raw_page in pages_text:
        page_text = re.sub(r"\s+", " ", raw_page).strip()
        if not page_text:
            continue

        # Partir en trozos seguros
        chunks, remaining = [], page_text
        while remaining:
            if len(remaining) <= 800:
                chunks.append(remaining)
                break
            cut = remaining[:800].rfind(" ")
            cut = cut if cut > 0 else 800
            chunks.append(remaining[:cut].strip())
            remaining = remaining[cut:].strip()

        translated_chunks = []
        for chunk in chunks:
            if chunk:
                resp = client.translation(chunk)
                # Manejo seguro igual que en el resumen
                if isinstance(resp, str):
                    translated_chunks.append(resp)
                elif hasattr(resp, "translation_text"):
                    translated_chunks.append(resp.translation_text)
                elif isinstance(resp, list) and len(resp) > 0 and isinstance(resp[0], dict):
                    translated_chunks.append(resp[0].get("translation_text", str(resp)))
                elif isinstance(resp, dict):
                    translated_chunks.append(resp.get("translation_text", str(resp)))
                else:
                    translated_chunks.append(str(resp))

        if translated_chunks:
            translated_pages.append(" ".join(translated_chunks))

    return "\n\n".join(translated_pages) if translated_pages else "(No se encontró texto traducible)"


# ─────────────────────────────────────────────────────────────
# GENERADOR DE PDF CON REPORTLAB
# ─────────────────────────────────────────────────────────────

def _build_pdf(title: str, subtitle: str, content: str, source_filename: str) -> bytes:
    """Genera un PDF formateado con el resultado del análisis IA."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=3 * cm,
        bottomMargin=2.5 * cm,
        title=title,
        author="PDF QUICK AI",
    )

    styles = getSampleStyleSheet()

    s_title = ParagraphStyle(
        "AITitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=HexColor("#0071e3"),
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    s_subtitle = ParagraphStyle(
        "AISubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#86868b"),
        spaceAfter=2,
    )
    s_source = ParagraphStyle(
        "AISource",
        parent=styles["Normal"],
        fontSize=9,
        textColor=HexColor("#86868b"),
        spaceAfter=16,
    )
    s_body = ParagraphStyle(
        "AIBody",
        parent=styles["Normal"],
        fontSize=11,
        leading=17,
        textColor=HexColor("#1d1d1f"),
        spaceAfter=4,
    )
    s_footer = ParagraphStyle(
        "AIFooter",
        parent=styles["Normal"],
        fontSize=8,
        textColor=HexColor("#86868b"),
        alignment=1,
    )

    story = []

    # ── Cabecera ──
    story.append(Paragraph(_esc(title), s_title))
    story.append(Paragraph(_esc(subtitle), s_subtitle))
    story.append(Paragraph(f"Fuente: {_esc(source_filename)}", s_source))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#eaeaea"), spaceAfter=14))

    # ── Cuerpo ──
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.25 * cm))
            continue
        story.append(Paragraph(_esc(line), s_body))

    # ── Pie ──
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#eaeaea"), spaceAfter=6))
    story.append(
        Paragraph(
            f"Generado por PDF QUICK · {date.today().strftime('%d/%m/%Y')}",
            s_footer,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _esc(text: str) -> str:
    """Escapa caracteres HTML especiales para ReportLab."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )
