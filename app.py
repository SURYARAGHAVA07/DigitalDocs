from flask import Flask, request, jsonify, send_file
import os
import json
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from flask_cors import CORS
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# File paths
BLOCKCHAIN_FILE = "blockchain.json"
CERTIFICATES_DIR = "certificates"
COLLEGE_LOGO_PATH = "E://IMAGES//CUTM_LOGO_TRANS_PNG-removebg-preview.png"  # Path to your college logo image

# Ensure directories exist
if not os.path.exists(CERTIFICATES_DIR):
    os.makedirs(CERTIFICATES_DIR)

# Load blockchain data
if os.path.exists(BLOCKCHAIN_FILE):
    with open(BLOCKCHAIN_FILE, "r") as file:
        blockchain = json.load(file)
else:
    blockchain = {"chain": [], "pending_certificates": []}

# Save blockchain data
def save_blockchain():
    with open(BLOCKCHAIN_FILE, "w") as file:
        json.dump(blockchain, file, indent=4)

# Add certificate
@app.route('/add_certificate', methods=['POST'])
def add_certificate():
    data = request.json
    required_fields = ["student_name", "student_id", "course", "institution", "duration"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    certificate = {
        "student_name": data["student_name"],
        "student_id": data["student_id"],
        "course": data["course"],
        "institution": data["institution"],
        "duration": data["duration"],
        "qr_code": None
    }

    blockchain["pending_certificates"].append(certificate)
    save_blockchain()
    return jsonify({"message": "Certificate added successfully."}), 200

# Mine a block
@app.route('/mine', methods=['POST'])
def mine():
    if not blockchain["pending_certificates"]:
        return jsonify({"message": "No certificates to mine."}), 400

    # Generate certificate QR codes and PDF files
    for certificate in blockchain["pending_certificates"]:
        qr_data = f'{certificate["student_id"]}_{certificate["student_name"]}'
        
        # Generate QR code
        qr = qrcode.make(qr_data)
        qr_path = os.path.join(CERTIFICATES_DIR, f'{qr_data}_qr.png')
        qr.save(qr_path)
        certificate["qr_code"] = qr_path
        
        # Generate PDF with college logo, centered text, and QR code at top-right
        pdf_path = os.path.join(CERTIFICATES_DIR, f'{qr_data}.pdf')
        c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # Add college logo (translucent background)
        if os.path.exists(COLLEGE_LOGO_PATH):
            c.drawImage(COLLEGE_LOGO_PATH, 150, 450, width=300, height=200, mask='auto')
        
        # Title (centered and large)
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.black)
        c.drawCentredString(300, 700, "Certificate of Completion")

        # Draw a horizontal line under the title
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(50, 685, 550, 685)

        # Add student and course details (left-aligned with consistent spacing)
        c.setFont("Helvetica-Bold", 12)
        y_position = 400

        # Function to draw text with center alignment and justified
        def draw_centered_text(text, y):
            text_width = c.stringWidth(text, "Helvetica-Bold", 12)
            c.drawString(300 - text_width / 2, y, text)

        draw_centered_text(f"Institution: {certificate['institution']}", y_position)
        draw_centered_text(f"Student Name: {certificate['student_name']}", y_position - 20)
        draw_centered_text(f"Student ID: {certificate['student_id']}", y_position - 40)
        draw_centered_text(f"Course: {certificate['course']}", y_position - 60)
        draw_centered_text(f"Duration: {certificate['duration']} months", y_position - 80)

        # Draw QR code at top-right corner
        c.drawImage(qr_path, 445, 690, width=100, height=100)

        # Save the PDF
        c.save()

        # Update certificate with the PDF path
        certificate["pdf_path"] = pdf_path

    # Create a new block with the certificates
    new_block = {
        "index": len(blockchain["chain"]) + 1,
        "certificates": blockchain["pending_certificates"]
    }

    blockchain["chain"].append(new_block)
    blockchain["pending_certificates"] = []
    save_blockchain()
    return jsonify({"message": "Block mined successfully.", "block": new_block}), 200

# View blockchain
@app.route('/chain', methods=['GET'])
def view_chain():
    return jsonify(blockchain), 200

# Generate and download certificate
@app.route('/generate_certificate', methods=['POST'])
def generate_certificate():
    data = request.json
    required_fields = ["student_name", "student_id", "course", "institution", "duration"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    # Generate QR code
    qr_data = f'{data["student_id"]}_{data["student_name"]}'
    qr = qrcode.make(qr_data)
    qr_path = os.path.join(CERTIFICATES_DIR, f'{qr_data}_qr.png')
    qr.save(qr_path)

    # Generate PDF with college logo, centered text, and QR code at top-right
    pdf_path = os.path.join(CERTIFICATES_DIR, f'{qr_data}.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Add college logo (translucent background)
    if os.path.exists(COLLEGE_LOGO_PATH):
        c.drawImage(COLLEGE_LOGO_PATH, 250, 450, width=200, height=200, mask='auto')

    # Title (centered and large)
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.black)
    c.drawCentredString(300, 700, "Certificate of Completion")

    # Draw a horizontal line under the title
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(50, 685, 550, 685)

    # Add student and course details (left-aligned with consistent spacing)
    c.setFont("Helvetica-Bold", 12)
    y_position = 630

    # Function to draw text with center alignment and justification
    def draw_centered_text(text, y):
        text_width = c.stringWidth(text, "Helvetica-Bold", 12)
        c.drawString(300 - text_width / 2, y, text)

    draw_centered_text(f"Institution: {data['institution']}", y_position)
    draw_centered_text(f"Student Name: {data['student_name']}", y_position - 20)
    draw_centered_text(f"Student ID: {data['student_id']}", y_position - 40)
    draw_centered_text(f"Course: {data['course']}", y_position - 60)
    draw_centered_text(f"Duration: {data['duration']} months", y_position - 80)

    # Draw QR code at top-right corner
    c.drawImage(qr_path, 100, 450, width=100, height=100)

    # Save the PDF
    c.save()

    return jsonify({"message": "Certificate generated.", "pdf_path": pdf_path}), 200

# Verify certificate
@app.route('/verify', methods=['POST'])
def verify_certificate():
    data = request.json
    required_fields = ["student_id", "qr_code"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    # Verify QR code
    expected_qr_data = f'{data["student_id"]}_{data["qr_code"]}'
    qr_path = os.path.join(CERTIFICATES_DIR, f'{expected_qr_data}_qr.png')
    if os.path.exists(qr_path):
        return jsonify({"message": "Certificate verified successfully."}), 200

    return jsonify({"error": "Certificate verification failed."}), 400

if __name__ == "__main__":
    app.run(debug=True)