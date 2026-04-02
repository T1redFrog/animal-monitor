from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import uuid
from datetime import datetime
from detector import AnimalDetector
from history import HistoryManager
from report import generate_excel_report, generate_pdf_report
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULTS_FOLDER'] = 'static/results'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 50MB

@app.errorhandler(RequestEntityTooLarge)
def too_large(e):
    return jsonify({'error': 'Файл слишком большой (максимум 200 МБ)'}), 413

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

detector = AnimalDetector()
history = HistoryManager()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не загружен'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Неподдерживаемый формат файла'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    is_video = ext in {'mp4', 'avi', 'mov'}
    result_filename = f"result_{filename}" if not is_video else f"result_{filename.rsplit('.', 1)[0]}.jpg"
    result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

    if is_video:
        detections, stats = detector.detect_video(filepath, result_path)
    else:
        detections, stats = detector.detect_image(filepath, result_path)

    record = {
        'id': uuid.uuid4().hex[:8],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'filename': file.filename,
        'type': 'video' if is_video else 'image',
        'detections': detections,
        'stats': stats,
        'result_image': result_filename
    }
    history.add(record)

    return jsonify({
        'success': True,
        'result_image': f'/static/results/{result_filename}',
        'detections': detections,
        'stats': stats,
        'record_id': record['id']
    })

@app.route('/history')
def get_history():
    return jsonify(history.get_all())

@app.route('/report/excel')
def report_excel():
    filepath = generate_excel_report(history.get_all())
    return send_from_directory('.', filepath, as_attachment=True, download_name='report.xlsx')

@app.route('/report/pdf')
def report_pdf():
    filepath = generate_pdf_report(history.get_all())
    return send_from_directory('.', filepath, as_attachment=True, download_name='report.pdf')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
