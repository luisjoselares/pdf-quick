import streamlit as st
import fitz
import os
import io
import re
from datetime import date
from groq import Groq # Cambiamos HuggingFace por Groq
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from utils.helpers import show_loader

# Capturamos la API Key desde los secretos de Streamlit Cloud de forma segura
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

# Actualizamos los modelos a los que soporta Groq (son súper rápidos)
MODELS = {
    "summarize": "llama-3.3-70b-versatile", # Excelente para resúmenes largos
    "analyze":   "mixtral-8x7b-32768",      # Muy bueno extrayendo puntos clave
    "translate": "llama-3.3-70b-versatile", # Llama 3 traduce espectacular
}

# Inicializamos el cliente de Groq (si hay llave)
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# ─────────────────────────────────────────────────────────────
# INTERFAZ
# ─────────────────────────────────────────────────────────────
def handle_ai_tools(t):
    st.markdown(f"## {t.get('ai_asst', 'Asistente IA')}")

    if not GROQ_API_KEY:
        st.warning(
            "⚠️ Para usar el Asistente IA, configura el Secret **GROQ_API_KEY** "
            "en los ajustes de Streamlit Cloud."
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
    """Limpia y trunca texto para enviarlo a la IA."""
    text = re.sub(r"[^\w\s.,;:!?()\'\"\-\náéíóúüñÁÉÍÓÚÜÑ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

def _summarize(text: str) -> str:
    """Genera un resumen ejecutivo usando Llama 3 en Groq."""
    clean_text = _clean(text, max_chars=12000)
    
    try:
        response = client.chat.completions.create(
            model=MODELS["summarize"],
            messages=[
                {"role": "system", "content": "Eres un experto en síntesis de información. Crea resúmenes ejecutivos claros, profesionales y bien estructurados."},
                {"role": "user", "content": f"Por favor, haz un resumen ejecutivo del siguiente texto. Mantén el idioma original:\n\n{clean_text}"}
            ],
            temperature=0.5,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error en el resumen (Groq): {str(e)}"


def _key_points(text: str) -> str:
    """Extrae 5 puntos clave usando Mixtral en Groq."""
    clean_text = _clean(text, max_chars=10000)
    
    try:
        response = client.chat.completions.create(
            model=MODELS["analyze"],
            messages=[
                {"role": "system", "content": "Eres un analista de documentos. Tu objetivo es identificar los conceptos más importantes."},
                {"role": "user", "content": f"Extrae los 5 puntos clave más relevantes del siguiente texto. Usa viñetas (•) y responde en el idioma original:\n\n{clean_text}"}
            ],
            temperature=0.3,
            max_tokens=600
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error en puntos clave (Groq): {str(e)}"


def _translate_pages(pages_text: list) -> str:
    """Traduce el contenido del PDF de Español a Inglés usando Llama 3."""
    # Combinamos las páginas para una traducción más coherente
    full_text = "\n\n".join(pages_text)
    clean_text = _clean(full_text, max_chars=12000)
    
    try:
        response = client.chat.completions.create(
            model=MODELS["translate"],
            messages=[
                {"role": "system", "content": "Eres un traductor profesional experto en el par de idiomas Español-Inglés."},
                {"role": "user", "content": f"Traduce el siguiente texto del Español al Inglés. Mantén un tono profesional y respeta el formato de párrafos:\n\n{clean_text}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error en traducción (Groq): {str(e)}"


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
