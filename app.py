from flask import Flask, send_from_directory, request, jsonify
import subprocess
import os
import sys  # ✅ add this

app = Flask(__name__)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Use the same Python interpreter as the current virtual environment
PYTHON_PATH = sys.executable

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/start_mouse', methods=['POST'])
def start_mouse():
    subprocess.Popen([PYTHON_PATH, os.path.join(BASE_DIR, "mouse.py")])
    return jsonify({"status": "Mouse Started"})

@app.route('/start_keyboard', methods=['POST'])
def start_keyboard():
    subprocess.Popen([PYTHON_PATH, os.path.join(BASE_DIR, "keyboard.py")])
    return jsonify({"status": "Keyboard Started"})

if __name__ == '__main__':
    app.run(debug=True)
