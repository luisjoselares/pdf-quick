import streamlit as st
from utils.helpers import load_css, get_translations
from controllers.pdf_controller import handle_merge, handle_split, handle_compress, handle_editor
from controllers.office_controller import handle_conversion
from controllers.security_controller import handle_security
from controllers.ai_controller import handle_ai_tools

st.set_page_config(
    page_title="PDF QUICK — Unir, Dividir, Convertir y Comprimir PDF Gratis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
    
     }   
)
load_css("style.css")

# ─── SEO: Meta tags + JSON-LD ─────────────────────────────────────────────────
st.markdown("""
<meta name="description" content="PDF QUICK: herramienta PDF online gratuita. Unir PDFs, dividir PDFs, comprimir PDFs, convertir PDF a Word, Excel, imágenes. Sin registro, procesado en memoria.">
<meta name="keywords" content="unir PDF, dividir PDF, comprimir PDF, convertir PDF a Word, PDF a Excel, PDF a imagen, editor PDF, herramientas PDF online gratis, fusionar PDF, separar PDF">
<meta name="robots" content="index, follow">
<meta property="og:title" content="PDF QUICK — Herramientas PDF Online Gratis">
<meta property="og:description" content="Unir, dividir, comprimir y convertir PDFs de forma gratuita. Sin registro, rápido y 100% privado.">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="PDF QUICK — Herramientas PDF Online">
<meta name="twitter:description" content="Unir, dividir, comprimir y convertir PDFs gratis. Sin registro.">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "PDF QUICK",
  "description": "Herramienta PDF online gratuita para unir, dividir, comprimir y convertir archivos PDF.",
  "applicationCategory": "UtilitiesApplication",
  "operatingSystem": "Web Browser",
  "inLanguage": ["es", "en"],
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "featureList": [
    "Unir PDFs", "Dividir PDFs", "Comprimir PDFs",
    "Convertir PDF a Word", "Convertir PDF a Excel",
    "Convertir PDF a imagen", "Editor visual PDF",
    "Marca de agua", "Numeración de páginas", "Asistente IA"
  ]
}
</script>
""", unsafe_allow_html=True)

# ─── ESTADO ────────────────────────────────────────────────────────────────────
if 'active_tool' not in st.session_state:
    st.session_state.active_tool = "merge"

# ─── SELECTOR DE IDIOMA ────────────────────────────────────────────────────────
col_spacer, col_lang = st.columns([10, 1])
with col_lang:
    current_idx = 0 if st.session_state.get("lang", "es") == "es" else 1
    lang = st.selectbox(
        "🌐",
        ["ES", "EN"],
        index=current_idx,
        label_visibility="visible",
        key="lang_selector"
    )
    if lang.lower() != st.session_state.get("lang", "es"):
        st.session_state.lang = lang.lower()
        st.rerun()

t = get_translations()

# ─── CABECERA ──────────────────────────────────────────────────────────────────
st.markdown("<h1 class='main-title'>PDF QU⚡CK</h1>", unsafe_allow_html=True)
st.markdown(f"<p class='sub-title'>{t['sub']}</p>", unsafe_allow_html=True)
st.markdown(f"<p class='sub-pills'>{t['sub_pills']}</p>", unsafe_allow_html=True)

# ─── PESTAÑAS PRINCIPALES ──────────────────────────────────────────────────────
tab_main, tab_all = st.tabs([
    f"⚡ {t['tab_quick']}",
    f"📂 {t['tab_all']}"
])

# ═══════════════════════════════════════════════════════════════════════════════
# PESTAÑA 1: ESENCIALES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_main:
    active = st.session_state.active_tool

    # Marcador invisible para scoping CSS
    st.markdown('<span class="nav-section-marker"></span>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(
            f"🗂️  {t['m_merge']}  ·  {t['nav_desc_merge']}",
            type="primary" if active == "merge" else "secondary",
            use_container_width=True,
            key="nav_merge"
        ):
            st.session_state.active_tool = "merge"
            st.rerun()
    with c2:
        if st.button(
            f"✂️  {t['m_split']}  ·  {t['nav_desc_split']}",
            type="primary" if active == "split" else "secondary",
            use_container_width=True,
            key="nav_split"
        ):
            st.session_state.active_tool = "split"
            st.rerun()
    with c3:
        if st.button(
            f"🔄  {t['m_editor']}  ·  {t['nav_desc_editor']}",
            type="primary" if active == "editor" else "secondary",
            use_container_width=True,
            key="nav_editor"
        ):
            st.session_state.active_tool = "editor"
            st.rerun()

    with st.container(border=True):
        if active == "merge":
            handle_merge(t)
        elif active == "split":
            handle_split(t)
        elif active == "editor":
            handle_editor(t)

# ═══════════════════════════════════════════════════════════════════════════════
# PESTAÑA 2: CONVERTIR & MÁS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_all:

    # ── Convertidor Universal ──
    st.markdown(f"#### 🔄 {t.get('conv_univ', 'Convertidor Universal')}")
    st.caption(t.get('conv_univ_desc', 'Convierte documentos entre formatos.'))

    c_to, c_sep, c_from = st.columns([1, 0.07, 1], gap="small")

    with c_to:
        st.markdown('<span class="conv-marker-to"></span>', unsafe_allow_html=True)
        with st.container(border=True):
            handle_conversion("to_pdf", t)

    with c_sep:
        st.markdown('<div class="conv-separator">→</div>', unsafe_allow_html=True)

    with c_from:
        st.markdown('<span class="conv-marker-from"></span>', unsafe_allow_html=True)
        with st.container(border=True):
            handle_conversion("from_pdf", t)

    st.markdown("---")

    # ── Herramientas Avanzadas ──
    st.markdown(f"#### 🛠️ {t.get('opt_sec', 'Optimización y Seguridad')}")
    st.caption(t.get('opt_sec_desc', 'Comprime, protege y mejora tus documentos.'))

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        with st.expander(f"🗜️ {t['m_comp']} — {t.get('comp_tagline', 'Reduce el peso')}", expanded=False):
            handle_compress(t)
    with col_b:
        with st.expander(f"🛡️ {t.get('sec_title', 'Seguridad')} — {t.get('sec_tagline', 'Marca y bloquea')}", expanded=False):
            handle_security(t)
    with col_c:
        with st.expander(f"🧠 {t.get('ai_asst', 'Asistente IA')} — {t.get('ai_tagline', 'Resume y analiza')}", expanded=False):
            handle_ai_tools(t)

    # ── SEO: Contenido indexable ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"""
<div class="seo-section">
  <h2>{t.get('seo_h2', '¿Qué puedes hacer con PDF QUICK?')}</h2>
  <div class="seo-grid">
    <div><strong>📄 {t.get('seo_merge_title', 'Unir PDFs')}</strong><br>{t.get('seo_merge_text', 'Combina varios archivos PDF en uno solo, en el orden que elijas.')}</div>
    <div><strong>✂️ {t.get('seo_split_title', 'Dividir PDFs')}</strong><br>{t.get('seo_split_text', 'Extrae páginas concretas o separa cada página en un archivo independiente.')}</div>
    <div><strong>🗜️ {t.get('seo_compress_title', 'Comprimir PDFs')}</strong><br>{t.get('seo_compress_text', 'Reduce el tamaño del archivo sin perder calidad visual.')}</div>
    <div><strong>🔄 {t.get('seo_convert_title', 'Convertir PDFs')}</strong><br>{t.get('seo_convert_text', 'Transforma PDFs a Word, Excel, PowerPoint, HTML, texto e imágenes.')}</div>
    <div><strong>🛡️ {t.get('seo_security_title', 'Seguridad PDF')}</strong><br>{t.get('seo_security_text', 'Añade marcas de agua, numera páginas y desbloquea documentos protegidos.')}</div>
    <div><strong>🧠 {t.get('seo_ai_title', 'Resumen con IA')}</strong><br>{t.get('seo_ai_text', 'Genera resúmenes ejecutivos y extrae puntos clave de cualquier PDF con inteligencia artificial.')}</div>
  </div>
  <p class="seo-note">{t.get('seo_privacy', '🔒 Todos los archivos se procesan en memoria. Ningún documento se almacena en nuestros servidores.')}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")  # Línea separadora elegante
st.markdown("### ⚡ Apoya a PDF QU⚡CK")
st.write("Esta herramienta es 100% gratuita y sin límites absurdos. Si te ahorró horas de trabajo, considera invitarme un café para ayudar a mantener los servidores encendidos. ¡Todo aporte suma!")

# Creamos dos columnas para que se vea balanceado
col_kofi, col_binance = st.columns(2, gap="large")

with col_kofi:
    st.markdown(
        """
        <a href="https://ko-fi.com/ldownloader" target="_blank" style="text-decoration: none;">
            <div style="background-color: #FF5E5B; color: white; padding: 15px 20px; border-radius: 12px; text-align: center; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s ease;">
                ☕ Invítame un café en Ko-fi
            </div>
        </a>
        """, 
        unsafe_allow_html=True
    )
    st.caption("Acepta tarjetas y PayPal de forma segura.")

with col_binance:
    st.markdown(
        """
        <div style="background-color: #FCD535; color: #1E2329; padding: 15px 20px; border-radius: 12px; text-align: center; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            🪙 Binance Pay ID: 422864557
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # El expander mantiene la interfaz limpia
    with st.expander("📷 Mostrar código QR para escanear"):
        try:
            # FIX: Usamos columnas para centrar y un ancho fijo (width=250) para matar el parpadeo
            col_izq, col_centro, col_der = st.columns([1, 2, 1])
            with col_centro:
                st.image("qr_binance.png", caption="Escanea desde tu app de Binance", width=250)
        except Exception:
            st.caption("⚠️ Falta subir el archivo 'qr_binance.png' al servidor.")
