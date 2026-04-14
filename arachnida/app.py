from flask import Flask, render_template, request, Response, jsonify
from PIL import Image
from PIL.ExifTags import TAGS
from spider.spider import spider
import piexif
import os

app = Flask(__name__)
SAVE_PATH = "static/data/"
stop_flag = False

@app.route("/")
def index():
    return (render_template("index.html"))

@app.route("/crawl")
def crawl():
    url = request.args.get("url")
    recursive = request.args.get("r", "false") == "true"
    max_depth = int(request.args.get("l", 5))
    os.makedirs(SAVE_PATH, exist_ok=True)

    def generate():
        global stop_flag
        stop_flag = False
        for filename in spider(url, recursive, max_depth, SAVE_PATH):
            if stop_flag:
                break
            yield f"data: {filename}\n\n"
        yield "data: DONE\n\n"
    return Response(generate(), mimetype="text/event-stream")

@app.route("/metadata")
def metadata():
    file = os.path.join(SAVE_PATH, request.args.get("file"))
    try:
        image = Image.open(file)
        exif_data = image._getexif()
        result = {}
        if (exif_data):
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                result[tag_name] = str(value)
        result["File Size"] = f"{os.path.getsize(file)} bytes"
        result["Created"] = str(os.path.getctime(file))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/strip", methods=["POST"])
def strip():
    file = os.path.join(SAVE_PATH, request.args.get("file"))
    try:
        piexif.remove(file)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/stop", methods=["POST"])
def stop():
    global stop_flag
    stop_flag = True
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
