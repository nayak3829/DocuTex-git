from flask import Flask, render_template, request, send_file
from converter import convert_docx_to_latex
import io
import zipfile


def make_pdf(text):
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    lines = safe.splitlines()[:48]
    content = "BT /F1 9 Tf 48 760 Td " + " ".join(f"({line[:105]}) Tj 0 -14 Td" for line in lines) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(content.encode('latin-1', 'replace'))} >>\\nstream\\n{content}\\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    ]
    pdf = "%PDF-1.4\\n"; offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf.encode('latin-1')))
        pdf += f"{index} 0 obj\\n{obj}\\nendobj\\n"
    xref = len(pdf.encode('latin-1'))
    pdf += "xref\\n0 6\\n0000000000 65535 f \\n" + "".join(f"{offset:010d} 00000 n \\n" for offset in offsets[1:])
    pdf += f"trailer\\n<< /Size 6 /Root 1 0 R >>\\nstartxref\\n{xref}\\n%%EOF"
    return pdf.encode('latin-1', 'replace')


app = Flask(__name__)

def render_result(latex_code="", error="", original_name=""):
    return render_template("index.html", latex_code=latex_code, error=error, original_name=original_name)


@app.route("/", methods=["GET", "POST"])
def home():
    latex_code = ""
    error = ""
    original_name = ""

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

    return render_result(latex_code, error, file.filename if file else "")


@app.route("/sample")
def sample():
    code = "\\documentclass{article}\n\\usepackage{amsmath}\n\\begin{document}\n\\section{A sample document}\nThis sample is ready to edit and export.\\par\n\\[ E = mc^2 \\]\n\\end{document}\n"
    return render_result(code, original_name="sample-document.docx")


@app.route("/download", methods=["POST"])
def download():
    code = request.form.get("latex_code", "")
    return send_file(io.BytesIO(code.encode("utf-8")), mimetype="text/plain", as_attachment=True, download_name="document.tex")


@app.route("/download/pdf", methods=["POST"])
def download_pdf():
    return send_file(io.BytesIO(make_pdf(request.form.get("latex_code", ""))), mimetype="application/pdf", as_attachment=True, download_name="document.pdf")


@app.route("/download/zip", methods=["POST"])
def download_zip():
    code = request.form.get("latex_code", "")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("document.tex", code)
        bundle.writestr("README.txt", "DocuTeX project\\nCompile document.tex with your LaTeX distribution.\\n")
    archive.seek(0)
    return send_file(archive, mimetype="application/zip", as_attachment=True, download_name="docutex-project.zip")


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)), debug=True)

