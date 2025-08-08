from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from ultralytics import YOLO
from PIL import Image
import io
import base64
import requests
from docx import Document
import PyPDF2
import traceback

# Captioning model (BLIP)
from transformers import BlipProcessor, BlipForConditionalGeneration, pipeline

app = Flask(__name__)
CORS(app)

# ===========================
# Load models at startup
# ===========================
print("Loading YOLO model...")
yolo_model = YOLO("yolov8n.pt")  # Change to your custom weights if needed

print("Loading BLIP captioning model...")
caption_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

print("Loading summarization model...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# ===========================
# Helper functions
# ===========================
def generate_caption(image: Image.Image):
    """Generate a caption using BLIP."""
    inputs = caption_processor(image, return_tensors="pt")
    out = caption_model.generate(**inputs, max_length=20)
    return caption_processor.decode(out[0], skip_special_tokens=True)


def pil_to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ===========================
# Routes
# ===========================
@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files["image"]
        try:
            image = Image.open(file.stream).convert("RGB")
        except Exception as e:
            return jsonify({"error": f"Unsupported image type: {str(e)}"}), 400

        # YOLO object detection
        results = yolo_model(image)
        detections = []
        annotated_image = None

        for r in results:
            for box in r.boxes:
                label = yolo_model.names[int(box.cls)]
                confidence = round(float(box.conf), 2)
                bbox = box.xyxy[0].tolist()
                detections.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": [round(v, 2) for v in bbox]
                })
            annotated_image_pil = r.plot()  # np array
            annotated_image = Image.fromarray(annotated_image_pil)

        annotated_base64 = None
        if annotated_image:
            annotated_base64 = pil_to_base64(annotated_image)

        # Captioning with BLIP
        try:
            caption = generate_caption(image)
        except Exception as e:
            caption = f"Caption generation failed: {str(e)}"

        return jsonify({
            "caption": caption,
            "detections": detections,
            "annotated_image": annotated_base64
        })

    except Exception as e:
        print("Analyze error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/summarize", methods=["POST", "OPTIONS"])
def summarize():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        text = ""
        if "file" in request.files:
            file = request.files["file"]
            if file.filename.lower().endswith(".pdf"):
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            elif file.filename.lower().endswith(".docx"):
                doc = Document(file)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            else:
                return jsonify({"error": "Unsupported file type"}), 400

        elif "url" in request.form:
            url = request.form["url"]
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                text = r.text
            except Exception as e:
                return jsonify({"error": f"URL fetch failed: {e}"}), 400

        else:
            return jsonify({"error": "No file or URL provided"}), 400

        if not text.strip():
            return jsonify({"error": "No text extracted"}), 400

        summary = summarizer(text, max_length=150, min_length=40, do_sample=False)
        return jsonify({"summary": summary[0]["summary_text"]})

    except Exception as e:
        print("Summarization error:", e)
        traceback.print_exc()
        return jsonify({"error": f"Summarization failed: {e}"}), 500


# ===========================
# Run app
# ===========================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
