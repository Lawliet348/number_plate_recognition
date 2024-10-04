from flask import Flask, render_template, jsonify, request
import base64
import easyocr
import re
import traceback
import cv2
import numpy as np

app = Flask(__name__)
reader = easyocr.Reader(["en"])

# Desired dimensions for the returned ROIs
desired_width = 323 * 2
desired_height = 108 * 2


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/capture", methods=["POST"])
def capture():
    try:
        # Get the image data from the POST request
        data = request.get_json()
        img_data = data["image"]

        # Decode base64 image data
        img_str = re.search(r"base64,(.*)", img_data).group(1)
        img_bytes = base64.b64decode(img_str)

        # Convert bytes to numpy array for OpenCV processing
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Convert the frame to RGB for EasyOCR processing
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = reader.readtext(img_rgb)
        out = "".join([result[1] for result in output])
        result = re.search(r"\d{4}", out)
        if result:
            roi_resized = cv2.resize(
                frame, (desired_width, desired_height), interpolation=cv2.INTER_LINEAR
            )
            _, buffer = cv2.imencode(".jpg", roi_resized)
            roi_base64 = base64.b64encode(buffer).decode("utf-8")

            # Extracted plate text
            plate_text = result.group()

            return jsonify({"plate_text": plate_text, "roi_base64": roi_base64})

        return jsonify({"error": "Number plate not detected"}), 400

    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/results")
def results():
    plate_text = request.args.get("plate_text")
    roi_base64 = request.args.get("roi_base64")
    return render_template("results.html", plate_text=plate_text, roi_base64=roi_base64)


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0")
    app.run(debug=True, host="0.0.0.0", port=8000, ssl_context=("cert.pem", "key.pem"))
    # app.run(debug=True, host="127.0.0.1", port=8000, ssl_context=("cert.pem", "key.pem"))
