import os
from flask import Flask, request, send_file, render_template, jsonify, send_from_directory

# Importación de controladores
from controllers.pdf_controller import PDFController
from controllers.ai_controller import AIController
from controllers.office_controller import OfficeController
from controllers.security_controller import SecurityController

app = Flask(__name__)

# Límite de subida configurado a 80 MB
app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024 

# ─────────────────────────────────────────────────────────────
# RUTAS DE LA API (HERRAMIENTAS CON NOMBRES DINÁMICOS)
# ─────────────────────────────────────────────────────────────

@app.route('/api/merge', methods=['POST'])
def api_merge():
    files = request.files.getlist("pdfs")
    if not files or files[0].filename == '': 
        return jsonify({"error": "No se subieron archivos"}), 400
    try:
        base_name = os.path.splitext(files[0].filename)[0]
        out = PDFController.merge(files)
        return send_file(out, 
                         mimetype='application/pdf', 
                         as_attachment=True, 
                         download_name=f"{base_name}_unido.pdf")
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/api/split', methods=['POST'])
def api_split():
    file = request.files.get("pdf")
    if not file: return jsonify({"error": "No se recibió archivo"}), 400
    
    base_name = os.path.splitext(file.filename)[0]
    mode = request.form.get("mode", "range")
    try:
        start = int(request.form.get("start_page", 1))
        end_str = request.form.get("end_page")
        end = int(end_str) if (end_str and end_str.strip()) else None
        
        out, mime, _ = PDFController.split(file, mode, start, end)
        
        ext = ".zip" if mode == "zip" else ".pdf"
        suffix = "_dividido" if mode == "zip" else "_extraido"
        
        return send_file(out, 
                         mimetype=mime, 
                         as_attachment=True, 
                         download_name=f"{base_name}{suffix}{ext}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/compress', methods=['POST'])
def api_compress():
    file = request.files.get("pdf")
    if not file or file.filename == '': 
        return jsonify({"error": "No se subió archivo"}), 400
    
    base_name = os.path.splitext(file.filename)[0]
    level = request.form.get("level", "Media")
    try:
        out, orig, comp = PDFController.compress(file, level)
        res = send_file(out, 
                        mimetype='application/pdf', 
                        as_attachment=True, 
                        download_name=f"{base_name}_comprimido.pdf")
        # Las cabeceras deben ser strings para evitar errores de servidor
        res.headers['X-Original-Size'] = str(orig)
        res.headers['X-Compressed-Size'] = str(comp)
        return res
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract-images', methods=['POST'])
def api_extract_images():
    file = request.files.get("pdf")
    if not file: 
        return jsonify({"error": "No se recibió archivo"}), 400
    
    base_name = os.path.splitext(file.filename)[0]
    try:
        out, count = PDFController.extract_images(file)
        return send_file(out, 
                         mimetype='application/zip', 
                         as_attachment=True, 
                         download_name=f"{base_name}_imagenes.zip")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai', methods=['POST'])
def api_ai():
    file = request.files.get("pdf")
    if not file or file.filename == '': 
        return jsonify({"error": "No se subió archivo"}), 400
    
    base_name = os.path.splitext(file.filename)[0]
    action = request.form.get("action")
    pages_str = request.form.get("pages", "1")
    
    try:
        pages = [int(p.strip()) for p in pages_str.split(",") if p.strip().isdigit()]
        out, _ = AIController.process_document(file, action, pages)
        return send_file(out, 
                         mimetype='application/pdf', 
                         as_attachment=True, 
                         download_name=f"{base_name}_analisis.pdf")
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def api_convert():
    action = request.form.get("action")
    try:
        if action == "img2pdf":
            files = request.files.getlist("files")
            if not files or files[0].filename == '': 
                return jsonify({"error": "No se subieron imágenes"}), 400
            base_name = os.path.splitext(files[0].filename)[0]
            out = OfficeController.multiple_img_to_pdf(files)
            return send_file(out, 
                             mimetype='application/pdf', 
                             as_attachment=True, 
                             download_name=f"{base_name}_galeria.pdf")
        
        file = request.files.get("file")
        if not file or file.filename == '': 
            return jsonify({"error": "No se subió archivo"}), 400
        
        base_name = os.path.splitext(file.filename)[0]
        
        if action == "pdf2word": out, mime, _ = OfficeController.pdf_to_word(file); suffix = "_convertido.docx"
        elif action == "pdf2excel": out, mime, _ = OfficeController.pdf_to_excel(file); suffix = "_convertido.xlsx"
        elif action == "pdf2pptx": out, mime, _ = OfficeController.pdf_to_pptx(file); suffix = "_convertido.pptx"
        elif action == "pdf2img": out, mime, _ = OfficeController.pdf_to_image(file, "PNG"); suffix = "_imagenes.zip"
        elif action == "office2pdf":
            out = OfficeController.office_to_pdf(file, file.filename)
            mime, suffix = "application/pdf", ".pdf"
        else: return jsonify({"error": "Acción inválida"}), 400
        
        return send_file(out, 
                         mimetype=mime, 
                         as_attachment=True, 
                         download_name=f"{base_name}{suffix}")
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/api/security', methods=['POST'])
def api_security():
    file = request.files.get("file")
    if not file or file.filename == '': return jsonify({"error": "No file"}), 400
    
    base_name = os.path.splitext(file.filename)[0]
    action = request.form.get("action")
    
    try:
        if action == "watermark":
            text = request.form.get("text", "CONFIDENCIAL")
            out = SecurityController.process_watermark(file, text, request.form.get("opacity", "0.3"), request.form.get("color", "#FF0000"))
            suffix = "_protegido.pdf"
        elif action == "pagination":
            out = SecurityController.process_pagination(file, request.form.get("pos", "Abajo Centro"))
            suffix = "_paginado.pdf"
        elif action == "unlock":
            out = SecurityController.process_unlock(file, request.form.get("password", ""))
            suffix = "_desbloqueado.pdf"
        else: return jsonify({"error": "Acción inválida"}), 400
        
        return send_file(out, 
                         mimetype='application/pdf', 
                         as_attachment=True, 
                         download_name=f"{base_name}{suffix}")
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN PARA GOOGLE (SITEMAP Y ROBOTS)
# ─────────────────────────────────────────────────────────────

@app.route('/sitemap.xml')
def serve_sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
def serve_robots():
    return send_from_directory('', 'robots.txt')

# ─────────────────────────────────────────────────────────────
# RUTAS DE NAVEGACIÓN Y SEO
# ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', 
        tool='home',
        title="PDF QU⚡CK - Unir, Dividir y Comprimir PDFs Gratis",
        description="Herramienta online gratuita y sin límites para manipular archivos PDF. Procesamiento rápido y seguro con Inteligencia Artificial.")

@app.route('/unir-pdf')
def route_merge():
    return render_template('index.html', 
        tool='merge',
        title="Unir PDF Online Gratis - PDF QU⚡CK",
        description="Combina múltiples archivos PDF en uno solo de forma rápida y segura.")

@app.route('/dividir-pdf')
def route_split():
    return render_template('index.html', 
        tool='split',
        title="Dividir PDF y Extraer Páginas - PDF QU⚡CK",
        description="Separa las páginas de tu PDF en un ZIP o extrae rangos específicos al instante.")

@app.route('/comprimir-pdf')
def route_compress():
    return render_template('index.html', 
        tool='compress',
        title="Comprimir PDF sin perder calidad - PDF QU⚡CK",
        description="Reduce el tamaño de tus archivos PDF optimizando imágenes y recursos internos.")

@app.route('/ia-pdf')
def route_ai():
    return render_template('index.html', 
        tool='ai',
        title="Analizar PDF con Inteligencia Artificial - PDF QU⚡CK",
        description="Resume o traduce tus documentos PDF usando Llama 3 en segundos.")

@app.route('/extraer-imagenes-pdf')
def route_extract_images():
    return render_template('index.html', 
        tool='extract_images',
        title="Extraer Imágenes de PDF Online Gratis - PDF QU⚡CK",
        description="Extrae todas las imágenes (PNG, JPG) de tu archivo PDF en alta calidad y descárgalas en un ZIP.")

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', tool='home'), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
