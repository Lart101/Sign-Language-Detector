from flask import Flask, render_template, request, jsonify, url_for
from ultralytics import YOLO
import cv2
import os
import base64
import numpy as np
import logging
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING)
app = Flask(__name__)

CORS(app)

app.config['DEBUG']=os.environ.get('FLASH_DEBUG')

# Load the trained YOLO model
model = YOLO("runs/detect/train14/weights/best.pt")

# Define the path to your sign language images
SIGN_LANGUAGE_IMAGES_DIR = "static/sign_language_images"

# Manual mappings for special cases (e.g., words)
special_mappings = {
    
}

# Dynamic mappings for letters A-Z
letter_mappings = {
    char.upper(): f"alphabet_{char.upper()}.jpg" for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
}

# Dynamic mappings for numbers 1-10
number_mappings = {
    str(num): f"number_{num}.jpg" for num in range(1, 11)
}

# Combine all mappings
sign_language_mapping = {**letter_mappings, **number_mappings, **special_mappings}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/detect_webcam', methods=['POST'])
def detect_webcam():
    try:
        # Parse incoming JSON request
        data = request.json
        image_data = data['image'].split(",")[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Perform object detection
        results = model(frame)
        annotated_frame = results[0].plot()

        detected_text = []
        boxes_data = []
        
        # Extract detection details and draw bounding boxes
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls)
                label = model.names[class_id]
                detected_text.append(label)
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                boxes_data.append({
                    "label": label,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                })
                
                # Draw bounding box on frame
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Convert annotated frame back to base64
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            "image": frame_base64,
            "text": " ".join(detected_text),
            "boxes": boxes_data
        })
    except Exception as e:
        logging.error(f"Error processing webcam detection: {str(e)}")
        return jsonify({"error": "Error processing webcam detection"}), 500



@app.route('/detect_image', methods=['POST'])
def detect_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save the uploaded file temporarily
    file_path = os.path.join("static/uploads", file.filename)
    file.save(file_path)

    # Perform object detection
    results = model(file_path)
    annotated_frame = results[0].plot()

    # Save the annotated image
    output_path = os.path.join("static/uploads", "annotated_" + file.filename)
    cv2.imwrite(output_path, annotated_frame)

    # Extract detected text
    detected_text = ""
    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls)  # Class ID of the detected object
            label = model.names[class_id]  # Get the class name from the model
            detected_text += label

    return jsonify({"image": output_path, "text": detected_text})

@app.route('/translate_text', methods=['POST'])
def translate_text():
    # Extract and clean the input text
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
        
    input_text = data.get("text", "").upper().strip()
    if not input_text:
        return jsonify({"error": "No input text provided"}), 400

    translated_images = []
    words = input_text.split()

    for word in words:
        if word in special_mappings:
            # Handle special words
            translated_images.extend(process_word(word, special_mappings))
        else:
            # Process individual characters
            for char in word:
                translated_images.extend(process_word(char, sign_language_mapping))

    return jsonify({"images": translated_images})

def process_word(word, mapping):
    """Helper function to process a word/character and return its image URL."""
    if word in mapping:
        image_filename = mapping[word]
        fs_path = os.path.join(SIGN_LANGUAGE_IMAGES_DIR, image_filename)
        
        if os.path.exists(fs_path):
            return [url_for('static', filename=f'sign_language_images/{image_filename}')]
        else:
            logging.error(f"Image missing: {fs_path}")
            return [url_for('static', filename='sign_language_images/placeholder.jpg')]
    else:
        logging.warning(f"Unsupported: '{word}'")
        return [url_for('static', filename='sign_language_images/placeholder.jpg')]

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    if not os.path.exists("static/uploads"):
        os.makedirs("static/uploads")
    if not os.path.exists(SIGN_LANGUAGE_IMAGES_DIR):
        os.makedirs(SIGN_LANGUAGE_IMAGES_DIR)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))