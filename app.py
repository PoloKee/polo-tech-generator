from flask import Flask, render_template, request, send_from_directory
import os
import webbrowser
from threading import Timer
from payroll_service import PayrollService

app = Flask(__name__)
OUTPUT_DIR = "TiffanyPageStubs"
service = PayrollService(output_dir=OUTPUT_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    frequency = request.form.get('frequency', 'biweekly')
    pattern = request.form.get('pattern', 'SECURE')
    
    try:
        files = service.generate_payroll(frequency=frequency, security_pattern=pattern)
        return render_template('index.html', files=files, message="Payroll generated successfully!")
    except Exception as e:
        return render_template('index.html', message=f"Error: {str(e)}")

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # In a desktop app scenario, we often want to open the browser automatically
    Timer(1, open_browser).start()
    app.run(port=5000, debug=False)
