from flask import Flask, render_template, request, send_file
from converter import convert_docx_to_latex
from pathlib import Path
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
                from docx import Document

                doc = Document(io.BytesIO(file.read()))
                lines = []

                for paragraph in doc.paragraphs:
                    text = paragraph.text.strip()
                    if text:
                        text = (text.replace("\\", r"\textbackslash{}")
                                    .replace("&", r"\&")
                                    .replace("%", r"\%")
                                    .replace("$", r"\$")
                                    .replace("#", r"\#")
                                    .replace("_", r"\_")
                                    .replace("{", r"\{")
                                    .replace("}", r"\}"))
                        lines.append(text + "\n\n")

                latex_code = (
                    "\\documentclass{article}\n"
                    "\\begin{document}\n\n"
                    + "".join(lines)
                    + "\\end{document}\n"
                )
            except Exception:
                error = "Could not read this file. Please try another DOCX file."

    return render_template(
        "index.html", latex_code=latex_code, error=error
    )

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
    app.run(debug=True)