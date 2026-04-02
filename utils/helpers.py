import streamlit as st

def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        pass

def show_loader(message, icon="⚡"):
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
            <div class="loader-container">
                <div class="processing-text">{icon} {message}...</div>
                <div class="loading-bar"></div>
            </div>
        """, unsafe_allow_html=True)
    return placeholder

def get_translations():
    if 'lang' not in st.session_state:
        st.session_state.lang = "es"

    LANGS = {
        "en": {
            # ── Marca / Header
            "title": "PDF QUICK",
            "sub": "Fast, free and private PDF tools.",
            "sub_pills": "MERGE · SPLIT · CONVERT · COMPRESS",

            # ── Pestañas
            "tab_quick": "Essentials",
            "tab_all": "Convert & More",

            # ── Botones de navegación + descripción
            "m_merge": "Merge",
            "m_split": "Split",
            "m_comp": "Compress",
            "m_conv": "Convert",
            "m_editor": "Editor",
            "nav_desc_merge": "Combine multiple PDFs",
            "nav_desc_split": "Extract or separate pages",
            "nav_desc_editor": "Rotate and delete pages",

            # ── Acciones
            "btn_proc": "Process",
            "download": "Download",
            "success": "Done!",
            "drop": "Drag your file here",
            "privacy_note": "Processed in memory. No files stored.",

            # ── Convertidor
            "to_pdf": "Convert TO PDF",
            "from_pdf": "Extract FROM PDF",
            "conv_univ": "Universal Converter",
            "conv_univ_desc": "Convert documents between formats — in both directions.",
            "p2w": "Word",
            "p2e": "Excel",
            "p2i": "Image",

            # ── Avanzado
            "opt_sec": "Optimization & Security",
            "opt_sec_desc": "Compress, protect and enhance your documents.",
            "sec_title": "Security",
            "ai_asst": "AI Assistant",
            "comp_tagline": "Reduce file size",
            "sec_tagline": "Watermark & lock",
            "ai_tagline": "Summarize & analyze",

            # ── How to use
            "how_to": "How to use",
            "step_1": "Upload your file",
            "step_2": "Adjust the options",
            "step_3": "Download the result",

            # ── Descripciones de herramienta
            "desc_merge": "Upload the PDFs you want to combine and sort them in any order.",
            "desc_split": "Upload a PDF, select the pages and extract them.",
            "desc_editor": "Rotate, delete or rearrange pages visually.",
            "desc_compress": "Choose the quality level and reduce the file size.",

            # ── SEO
            "seo_h2": "What can you do with PDF QUICK?",
            "seo_merge_title": "Merge PDFs",
            "seo_merge_text": "Combine multiple PDF files into one, in the order you choose.",
            "seo_split_title": "Split PDFs",
            "seo_split_text": "Extract specific pages or separate each page into an individual file.",
            "seo_compress_title": "Compress PDFs",
            "seo_compress_text": "Reduce file size without significant loss of visual quality.",
            "seo_convert_title": "Convert PDFs",
            "seo_convert_text": "Transform PDFs to Word, Excel, PowerPoint, HTML, text and images.",
            "seo_security_title": "PDF Security",
            "seo_security_text": "Add watermarks, number pages and unlock password-protected documents.",
            "seo_ai_title": "AI Summary",
            "seo_ai_text": "Generate executive summaries and extract key points from any PDF using AI.",
            "seo_privacy": "🔒 All files are processed in memory. No document is stored on our servers.",
            # ── Support / Donaciones
            "support_title": "Support PDF QU⚡CK",
            "support_desc": "This tool is 100% free and has no absurd limits. If it saved you hours of work, consider buying me a coffee to help keep the servers running. Every contribution counts!",
            "kofi_btn": "Buy me a coffee on Ko-fi",
            "kofi_caption": "Accepts cards and PayPal securely.",
            "qr_expander": "Show QR code to scan",
            "qr_caption": "Scan from your Binance app",
            "qr_error": "Missing 'qr_binance.png' file on the server.",
        },
        "es": {
            # ── Marca / Header
            "title": "PDF QUICK",
            "sub": "Herramientas PDF rápidas, gratuitas y privadas.",
            "sub_pills": "UNIR · DIVIDIR · CONVERTIR · COMPRIMIR",

            # ── Pestañas
            "tab_quick": "Esenciales",
            "tab_all": "Convertir & Más",

            # ── Botones de navegación + descripción
            "m_merge": "Unir",
            "m_split": "Dividir",
            "m_comp": "Comprimir",
            "m_conv": "Convertir",
            "m_editor": "Editor",
            "nav_desc_merge": "Combina varios PDFs",
            "nav_desc_split": "Extrae o separa páginas",
            "nav_desc_editor": "Rota y elimina páginas",

            # ── Acciones
            "btn_proc": "Procesar",
            "download": "Descargar",
            "success": "Listo",
            "drop": "Arrastra tu archivo aquí",
            "privacy_note": "Procesado en memoria. No se guardan archivos.",

            # ── Convertidor
            "to_pdf": "Convertir A PDF",
            "from_pdf": "Extraer DESDE PDF",
            "conv_univ": "Convertidor Universal",
            "conv_univ_desc": "Convierte documentos entre formatos en ambas direcciones.",
            "p2w": "Word",
            "p2e": "Excel",
            "p2i": "Imagen",

            # ── Avanzado
            "opt_sec": "Optimización y Seguridad",
            "opt_sec_desc": "Comprime, protege y mejora tus documentos.",
            "sec_title": "Seguridad",
            "ai_asst": "Asistente IA",
            "comp_tagline": "Reduce el peso",
            "sec_tagline": "Marca y protege",
            "ai_tagline": "Resume y analiza",

            # ── How to use
            "how_to": "Cómo usar",
            "step_1": "Sube tu archivo",
            "step_2": "Ajusta las opciones",
            "step_3": "Descarga el resultado",

            # ── Descripciones de herramienta
            "desc_merge": "Sube los PDFs que quieres combinar y ordénalos como prefieras.",
            "desc_split": "Sube un PDF, elige las páginas y extráelas al instante.",
            "desc_editor": "Rota, elimina o reordena páginas de forma visual.",
            "desc_compress": "Elige el nivel de calidad y reduce el tamaño del archivo.",

            # ── SEO
            "seo_h2": "¿Qué puedes hacer con PDF QUICK?",
            "seo_merge_title": "Unir PDFs",
            "seo_merge_text": "Combina varios archivos PDF en uno solo, en el orden que elijas.",
            "seo_split_title": "Dividir PDFs",
            "seo_split_text": "Extrae páginas concretas o separa cada página en un archivo independiente.",
            "seo_compress_title": "Comprimir PDFs",
            "seo_compress_text": "Reduce el tamaño del archivo sin pérdida significativa de calidad visual.",
            "seo_convert_title": "Convertir PDFs",
            "seo_convert_text": "Transforma PDFs a Word, Excel, PowerPoint, HTML, texto e imágenes.",
            "seo_security_title": "Seguridad PDF",
        
            "seo_security_text": "Añade marcas de agua, numera páginas y desbloquea documentos protegidos.",
            "seo_ai_title": "Resumen con IA",
            "seo_ai_text": "Genera resúmenes ejecutivos y extrae puntos clave de cualquier PDF con inteligencia artificial.",
            "seo_privacy": "🔒 Todos los archivos se procesan en memoria. Ningún documento se almacena en nuestros servidores.",
            # ── Support / Donaciones
            "support_title": "Apoya a PDF QU⚡CK",
            "support_desc": "Esta herramienta es 100% gratuita y sin límites absurdos. Si te ahorró horas de trabajo, considera invitarme un café para ayudar a mantener los servidores encendidos. ¡Todo aporte suma!",
            "kofi_btn": "Invítame un café en Ko-fi",
            "kofi_caption": "Acepta tarjetas y PayPal de forma segura.",
            "qr_expander": "Mostrar código QR para escanear",
            "qr_caption": "Escanea desde tu app de Binance",
            "qr_error": "Falta subir el archivo 'qr_binance.png' al servidor.",
        }
    }
    return LANGS[st.session_state.lang]
