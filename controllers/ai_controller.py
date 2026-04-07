import fitz
import os
import io
import re
from datetime import date
from groq import Groq
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor

# Modelos soportados por Groq
MODELS = {
    "summarize": "llama-3.3-70b-versatile",
    "analyze":   "mixtral-8x7b-32768",
    "translate": "llama-3.3-70b-versatile",
}

class AIController:
    """
    Controlador puro para manejar la IA.
    Sin dependencias de Streamlit.
    """

    @staticmethod
    def get_client():
        """Inicializa el cliente de Groq leyendo la variable de entorno de Render."""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("No se configuró la GROQ_API_KEY en las variables de entorno del servidor.")
        return Groq(api_key=api_key)

    @staticmethod
    def process_document(file, action, selected_pages):
        """
        Lee el PDF, extrae el texto de las páginas indicadas, 
        lo procesa con Groq y devuelve un PDF formateado con el resultado.
        """
        # Leemos el archivo enviado desde Flask
        file_bytes = file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        pages_text = []
        # Fitz usa índice basado en 0, el usuario envía basado en 1
        for p_num in sorted(selected_pages):
            idx = p_num - 1
            if 0 <= idx < len(doc):
                text = doc[idx].get_text()
                if text.strip():
                    pages_text.append(text)
        doc.close()

        if not pages_text:
            raise ValueError("No se detectó texto legible en las páginas seleccionadas.")

        pages_str = ", ".join(map(str, sorted(selected_pages)))
        combined_text = "\n".join(pages_text)

        # ── Ejecutar Acción IA ─────────────────────────────────
        if action == "resumen":
            result_text = AIController._summarize(combined_text)
            title       = "Resumen Ejecutivo"
            subtitle    = f"Análisis de la(s) página(s): {pages_str}"
            filename    = f"resumen_{file.filename}"

        elif action == "puntos_clave":
            result_text = AIController._key_points(combined_text)
            title       = "Puntos Clave del Documento"
            subtitle    = f"Extraído de la(s) página(s): {pages_str}"
            filename    = f"puntos_clave_{file.filename}"

        elif action == "traduccion":
            result_text = AIController._translate_pages(pages_text)
            title       = "Documento Traducido (ES → EN)"
            subtitle    = f"Translated page(s): {pages_str} · PDF QUICK AI"
            filename    = f"traduccion_{file.filename}"
        else:
            raise ValueError("Acción de IA no válida.")

        # ── Generar PDF de salida ──────────────────────────────
        pdf_bytes = AIController._build_pdf(title, subtitle, result_text, file.filename)
        return pdf_bytes, filename

    # ─────────────────────────────────────────────────────────────
    # MOTORES IA INTERNOS
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def _clean(text: str, max_chars: int = 15000) -> str:
        text = re.sub(r"[^\w\s.,;:!?()\'\"\-\náéíóúüñÁÉÍÓÚÜÑ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]

    @staticmethod
    def _summarize(text: str) -> str:
        client = AIController.get_client()
        clean_text = AIController._clean(text, max_chars=12000)
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

    @staticmethod
    def _key_points(text: str) -> str:
        client = AIController.get_client()
        clean_text = AIController._clean(text, max_chars=10000)
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

    @staticmethod
    def _translate_pages(pages_text: list) -> str:
        client = AIController.get_client()
        full_text = "\n\n".join(pages_text)
        clean_text = AIController._clean(full_text, max_chars=12000)
        response = client.chat.completions.create(
            model=MODELS["translate"],
            messages=[
                {"role": "system", "content": "Eres un traductor profesional experto en el par de idiomas Español-Inglés."},
                {"role": "user", "content": f"Traduce el siguiente texto del Español al Inglés. Mantén un tono profesional y respeta el formato de párrafos:\n\n{clean_text}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    # ─────────────────────────────────────────────────────────────
    # GENERADOR DE PDF CON REPORTLAB
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def _build_pdf(title: str, subtitle: str, content: str, source_filename: str) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, rightMargin=2.5*cm, leftMargin=2.5*cm,
            topMargin=3*cm, bottomMargin=2.5*cm, title=title, author="PDF QUICK AI"
        )
        styles = getSampleStyleSheet()
        s_title = ParagraphStyle("AITitle", parent=styles["Title"], fontSize=20, textColor=HexColor("#0071e3"), spaceAfter=4, fontName="Helvetica-Bold")
        s_subtitle = ParagraphStyle("AISubtitle", parent=styles["Normal"], fontSize=10, textColor=HexColor("#86868b"), spaceAfter=2)
        s_source = ParagraphStyle("AISource", parent=styles["Normal"], fontSize=9, textColor=HexColor("#86868b"), spaceAfter=16)
        s_body = ParagraphStyle("AIBody", parent=styles["Normal"], fontSize=11, leading=17, textColor=HexColor("#1d1d1f"), spaceAfter=4)
        s_footer = ParagraphStyle("AIFooter", parent=styles["Normal"], fontSize=8, textColor=HexColor("#86868b"), alignment=1)

        story = []
        story.append(Paragraph(AIController._esc(title), s_title))
        story.append(Paragraph(AIController._esc(subtitle), s_subtitle))
        story.append(Paragraph(f"Fuente: {AIController._esc(source_filename)}", s_source))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#eaeaea"), spaceAfter=14))

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.25 * cm))
                continue
            story.append(Paragraph(AIController._esc(line), s_body))

        story.append(Spacer(1, 1 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#eaeaea"), spaceAfter=6))
        story.append(Paragraph(f"Generado por PDF QUICK · {date.today().strftime('%d/%m/%Y')}", s_footer))

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _esc(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
