import os
from flask import Flask, render_template, request, send_file, jsonify

# Importación de tus controladores
from controllers.pdf_controller import PDFController
from controllers.ai_controller import AIController
from controllers.office_controller import OfficeController
from controllers.security_controller import SecurityController

app = Flask(__name__)

# Límite de subida configurado a 80 MB
app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024 

# ─────────────────────────────────────────────────────────────
# RUTA DEL FRONTEND
# ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ─────────────────────────────────────────────────────────────
# RUTAS DE LA API (HERRAMIENTAS BÁSICAS)
# ─────────────────────────────────────────────────────────────
@app.route('/api/merge', methods=['POST'])
def api_merge():
    files = request.files.getlist("pdfs")
    if not files or files[0].filename == '': 
        return jsonify({"error": "No se subieron archivos"}), 400
    try:
        out = PDFController.merge(files)
        return send_file(out, mimetype='application/pdf', as_attachment=True, download_name='unido.pdf')
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/api/split', methods=['POST'])
def api_split():
    file = request.files.get("pdf")
    if not file: return jsonify({"error": "No file"}), 400
    
    # Aseguramos que el modo sea 'range' por defecto
    mode = request.form.get("mode", "range")
    try:
        start = int(request.form.get("start_page", 1))
        end_str = request.form.get("end_page")
        end = int(end_str) if (end_str and end_str.strip()) else None
        
        out, mime, name = PDFController.split(file, mode, start, end)
        return send_file(out, mimetype=mime, as_attachment=True, download_name=name)
    except Exception as e:
        return jsonify({"error": f"Error al dividir: {str(e)}"}), 500
        
@app.route('/api/compress', methods=['POST'])
def api_compress():
    file = request.files.get("pdf")
    if not file or file.filename == '': 
        return jsonify({"error": "No se subió archivo"}), 400
        
    level = request.form.get("level", "Media")
    try:
        out, orig, comp = PDFController.compress(file, level)
        res = send_file(out, mimetype='application/pdf', as_attachment=True, download_name='comprimido.pdf')
        res.headers['X-Original-Size'] = orig
        res.headers['X-Compressed-Size'] = comp
        return res
    except Exception as e: 
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# RUTA DE INTELIGENCIA ARTIFICIAL
# ─────────────────────────────────────────────────────────────
@app.route('/api/ai', methods=['POST'])
def api_ai():
    file = request.files.get("pdf")
    if not file or file.filename == '': 
        return jsonify({"error": "No se subió archivo"}), 400
        
    action = request.form.get("action")
    pages_str = request.form.get("pages", "1")
    
    try:
        pages = [int(p.strip()) for p in pages_str.split(",") if p.strip().isdigit()]
        out, name = AIController.process_document(file, action, pages)
        return send_file(out, mimetype='application/pdf', as_attachment=True, download_name=name)
    except Exception as e: 
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# RUTA DE CONVERSIONES (OFFICE)
# ─────────────────────────────────────────────────────────────
@app.route('/api/convert', methods=['POST'])
def api_convert():
    action = request.form.get("action")
    
    try:
        # Caso especial para la unión de múltiples imágenes
        if action == "img2pdf":
            files = request.files.getlist("files")
            if not files or files[0].filename == '': 
                return jsonify({"error": "No se subieron imágenes"}), 400
            out = OfficeController.multiple_img_to_pdf(files)
            return send_file(out, mimetype='application/pdf', as_attachment=True, download_name='imagenes.pdf')
        
        # Flujo estándar para 1 solo archivo
        file = request.files.get("file")
        if not file or file.filename == '': 
            return jsonify({"error": "No se subió archivo"}), 400
        
        if action == "pdf2word":
            out, mime, name = OfficeController.pdf_to_word(file)
        elif action == "pdf2excel":
            out, mime, name = OfficeController.pdf_to_excel(file)
        elif action == "pdf2pptx":
            out, mime, name = OfficeController.pdf_to_pptx(file)
        elif action == "pdf2html":
            out, mime, name = OfficeController.pdf_to_html(file)
        elif action == "pdf2txt":
            out, mime, name = OfficeController.pdf_to_txt(file)
        elif action == "pdf2img":
            out, mime, name = OfficeController.pdf_to_image(file, "PNG")
        elif action == "office2pdf":
            out = OfficeController.office_to_pdf(file, file.filename)
            mime = "application/pdf"
            name = f"{os.path.splitext(file.filename)[0]}.pdf"
        else:
            return jsonify({"error": "Acción de conversión inválida"}), 400
        
        return send_file(out, mimetype=mime, as_attachment=True, download_name=name)
    except Exception as e: 
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# RUTA DE SEGURIDAD
# ─────────────────────────────────────────────────────────────
@app.route('/api/security', methods=['POST'])
def api_security():
    file = request.files.get("file")
    if not file or file.filename == '': 
        return jsonify({"error": "No se subió archivo"}), 400
        
    action = request.form.get("action")
    
    try:
        if action == "watermark":
            text = request.form.get("text", "CONFIDENCIAL")
            opacity = request.form.get("opacity", "0.3")
            color = request.form.get("color", "#FF0000")
            out = SecurityController.process_watermark(file, text, opacity, color)
        elif action == "pagination":
            pos = request.form.get("pos", "Abajo Centro")
            out = SecurityController.process_pagination(file, pos)
        elif action == "unlock":
            pwd = request.form.get("password", "")
            out = SecurityController.process_unlock(file, pwd)
        else:
            return jsonify({"error": "Acción de seguridad inválida"}), 400
        
        return send_file(out, mimetype='application/pdf', as_attachment=True, download_name=f'sec_{file.filename}')
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────────────────────
# RUTA DE PRIVACIDAD
# ─────────────────────────────────────────────────────────────
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')
# ─────────────────────────────────────────────────────────────
# ARRANQUE DEL SERVIDOR
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
