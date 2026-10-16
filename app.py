from flask import Flask, render_template, request, send_file
from converter import convert_docx_to_latex
import io

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    latex_code = ""
    error = ""

    if request.method == "POST":
        file = request.files.get("document")

        if not file or not file.filename:
            error = "Please select a Word document."
        elif not file.filename.lower().endswith(".docx"):
            error = "Please upload a .docx file."
        else:
            try:
                latex_code = convert_docx_to_latex(io.BytesIO(file.read()))
            except Exception:
                error = "Could not read this file. Please try another DOCX file."

    return render_template("index.html", latex_code=latex_code, error=error)


@app.route("/download", methods=["POST"])
def download():
    code = request.form.get("latex_code", "")
    return send_file(
        io.BytesIO(code.encode("utf-8")),
        mimetype="text/plain",
        as_attachment=True,
        download_name="document.tex"
    )

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)), debug=True)

