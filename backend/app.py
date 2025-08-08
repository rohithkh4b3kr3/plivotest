# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from ultralytics import YOLO
# from transformers import pipeline
# from PIL import Image, ImageDraw, ImageFont
# import io
# import base64

# app = Flask(__name__)
# CORS(app)

# yolo = YOLO("yolov8n.pt")

# # captioner = pipeline("image-captioning", model="Salesforce/blip-image-captioning-base")
# captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

# def pil_to_base64(img):
#     buf = io.BytesIO()
#     img.save(buf, format="PNG")
#     byte_im = buf.getvalue()
#     return base64.b64encode(byte_im).decode("utf-8")

# @app.route("/analyze", methods=["POST"])
# def analyze():
#     if "image" not in request.files:
#         return jsonify({"error": "No image file provided (field name must be 'image')"}), 400

#     file = request.files["image"]
#     image_bytes = file.read()
#     img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

#     # 1) Caption the image
#     try:
#         cap_out = captioner(img)
#         # pipeline may return list of dicts with 'generated_text' or 'caption'
#         caption_text = None
#         if isinstance(cap_out, list) and len(cap_out) > 0:
#             first = cap_out[0]
#             caption_text = first.get("generated_text") or first.get("caption") or str(first)
#         else:
#             caption_text = str(cap_out)
#     except Exception as e:
#         caption_text = f"(captioning failed: {e})"

#     # 2) Run YOLO detections
#     try:
#         results = yolo(image_bytes, imgsz=640)  # pass raw bytes or path
#         # results is a list-like; look at first
#         res = results[0]

#         detections = []
#         # res.boxes has fields: xyxy, conf, cls
#         for box in res.boxes:
#             # ultralytics Boxes give tensors; convert to python numbers
#             xyxy = box.xyxy.tolist()[0] if hasattr(box.xyxy, 'tolist') else [float(x) for x in box.xyxy]
#             conf = float(box.conf.tolist()[0]) if hasattr(box.conf, 'tolist') else float(box.conf)
#             cls_id = int(box.cls.tolist()[0]) if hasattr(box.cls, 'tolist') else int(box.cls)
#             label = res.names.get(cls_id, str(cls_id))
#             detections.append({
#                 "label": label,
#                 "confidence": round(conf, 3),
#                 "bbox": [round(x, 1) for x in xyxy],  # [x1,y1,x2,y2]
#             })

#         # draw annotated image
#         draw = ImageDraw.Draw(img)
#         try:
#             font = ImageFont.load_default()
#         except:
#             font = None

#         for d in detections:
#             x1, y1, x2, y2 = d["bbox"]
#             draw.rectangle([x1, y1, x2, y2], width=2)
#             text = f"{d['label']} {d['confidence']}"
#             text_size = draw.textsize(text, font=font) if font else (0, 0)
#             draw.rectangle([x1, y1 - text_size[1] - 4, x1 + text_size[0] + 4, y1], fill=(255, 255, 255))
#             draw.text((x1 + 2, y1 - text_size[1] - 2), text, fill=(0, 0, 0), font=font)

#         annotated_b64 = pil_to_base64(img)

#         return jsonify({
#             "caption": caption_text,
#             "detections": detections,
#             "annotated_image": annotated_b64,
#         })

#     except Exception as e:
#         return jsonify({
#             "caption": caption_text,
#             "detections": [],
#             "annotated_image": None,
#             "error": f"YOLO failed: {e}",
#         }), 500


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)


#     # ap2_c385fb3c-78ec-4e33-87bf-6533843e92e9
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

# Captioning model (BLIP)
from transformers import BlipProcessor, BlipForConditionalGeneration, pipeline

app = Flask(__name__)
CORS(app)

# Load YOLO model
yolo_model = YOLO("yolov8n.pt")  # use your custom weights if needed

# Load BLIP caption model
caption_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


def generate_caption(image: Image.Image):
    """Generate a caption using BLIP."""
    inputs = caption_processor(image, return_tensors="pt")
    out = caption_model.generate(**inputs, max_length=20)
    return caption_processor.decode(out[0], skip_special_tokens=True)


def pil_to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@app.route("/analyze", methods=["POST"])
def analyze():
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
        annotated_image_pil = r.plot()  # returns np array
        annotated_image = Image.fromarray(annotated_image_pil)

    # Convert annotated image to base64
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


@app.route("/summarize", methods=["POST"])
def summarize():
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

    try:
        summary = summarizer(text, max_length=150, min_length=40, do_sample=False)
        return jsonify({"summary": summary[0]["summary_text"]})
    except Exception as e:
        return jsonify({"error": f"Summarization failed: {e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
