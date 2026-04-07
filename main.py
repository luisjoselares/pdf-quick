import os
import json
from flask import Flask, render_template, request, send_file, jsonify
from controllers.pdf_controller import PDFController
from controllers.ai_controller import AIController
from controllers.security_controller import SecurityController
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024
# ─────────────────────────────────────────────────────────────
# RUTA DEL FRONTEND (LO QUE GOOGLE Y EL USUARIO VEN)
# ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    # Devuelve el HTML puro. Esto elimina el "Error de redirección" de Google.
    return render_template('index.html')


# ─────────────────────────────────────────────────────────────
# RUTAS DE LA API (PROCESAMIENTO DE PDFs)
# ─────────────────────────────────────────────────────────────

@app.route('/api/merge', methods=['POST'])
def api_merge():
    # Recibimos múltiples archivos con la etiqueta "pdfs"
    files = request.files.getlist("pdfs")
    if not files or files[0].filename == '':
        return jsonify({"error": "No se subieron archivos"}), 400

    try:
        output_pdf = PDFController.merge(files)
        return send_file(
            output_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='merged_pdfquick.pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/split', methods=['POST'])
def api_split():
    file = request.files.get("pdf")
    if not file or file.filename == '':
        return jsonify({"error": "No se subió ningún archivo"}), 400

    # Extraemos las opciones desde el formulario HTML
    mode = request.form.get("mode", "range")
    start_page = int(request.form.get("start_page", 1))
    
    end_page = request.form.get("end_page")
    if end_page:
        end_page = int(end_page)

    try:
        output, mime_type, filename = PDFController.split(file, mode, start_page, end_page)
        return send_file(
            output,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/compress', methods=['POST'])
def api_compress():
    file = request.files.get("pdf")
    if not file or file.filename == '':
        return jsonify({"error": "No se subió ningún archivo"}), 400

    level = request.form.get("level", "Media")

    try:
        output, original_size, compressed_size = PDFController.compress(file, level)
        response = send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'min_{file.filename}'
        )
        # Pasamos estadísticas de compresión ocultas en las cabeceras por si quieres mostrarlas
        response.headers['X-Original-Size'] = original_size
        response.headers['X-Compressed-Size'] = compressed_size
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/edit', methods=['POST'])
def api_edit():
    file = request.files.get("pdf")
    if not file or file.filename == '':
        return jsonify({"error": "No se subió ningún archivo"}), 400

    # La configuración de qué páginas rotar/eliminar llega como texto JSON
    pages_config_str = request.form.get("pages_config")
    if not pages_config_str:
        return jsonify({"error": "Falta la configuración de páginas"}), 400

    try:
        pages_config = json.loads(pages_config_str)
        output = PDFController.edit(file, pages_config)
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'edit_{file.filename}'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/api/ai', methods=['POST'])
def api_ai():
    file = request.files.get("pdf")
    if not file or file.filename == '':
        return jsonify({"error": "No se subió ningún archivo"}), 400

    action = request.form.get("action") # "resumen", "puntos_clave", o "traduccion"
    pages_str = request.form.get("pages", "") # Ejemplo: "1,2,3"
    
    if not action or not pages_str:
        return jsonify({"error": "Faltan parámetros (acción o páginas)"}), 400

    try:
        # Convertimos "1,2,3" en una lista de enteros: [1, 2, 3]
        selected_pages = [int(p.strip()) for p in pages_str.split(",") if p.strip().isdigit()]
        
        # Procesamos
        output_buffer, out_filename = AIController.process_document(file, action, selected_pages)
        
        return send_file(
            output_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=out_filename
        )
    except Exception as e:
        # Si la API Key no está, o Groq falla, Flask devuelve un error 500 limpio
        return jsonify({"error": str(e)}), 500
@app.route('/api/watermark', methods=['POST'])
def api_watermark():
    file = request.files.get("pdf")
    text = request.form.get("text", "CONFIDENCIAL")
    opacity = request.form.get("opacity", 0.3)
    color = request.form.get("color", "#FF0000")

    try:
        output_buffer = SecurityController.process_watermark(file, text, opacity, color)
        return send_file(
            output_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='watermarked.pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ─────────────────────────────────────────────────────────────
# ARRANQUE DEL SERVIDOR PARA RENDER.COM
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Render asigna dinámicamente un puerto en la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
