from jinja2 import Template
import os
import tempfile
import logging
from azure.functions import HttpRequest, HttpResponse
from weasyprint import HTML

def main(req: HttpRequest) -> HttpResponse:
    try:
        data = req.get_json()
        
        if not data:

            return HttpResponse("JSON data not provided", status_code=400)

        logging.info(data)

        # Les HTML-templaten
        with open("template.html", "r") as template_file:
            template = Template(template_file.read())

        # Generer HTML
        html_content = template.render(data=data)

        # Opprett en midlertidig HTML-fil
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as html_file:
            html_file.write(html_content.encode("utf-8"))

        # Opprett en midlertidig PDF-fil
        pdf_file = html_file.name.replace(".html", ".pdf")

        # Generer PDF fra HTML
        HTML(string=html_content).write_pdf(pdf_file)

        # Les PDF-innholdet og returner det som en respons
        with open(pdf_file, "rb") as pdf:
            pdf_content = pdf.read()

        # Rydd opp i midlertidige filer
        os.remove(html_file.name)
        os.remove(pdf_file)

        response = HttpResponse(pdf_content, mimetype="application/pdf", status_code=200)
        response.headers["Content-Disposition"] = 'attachment; filename="pasientjournal.pdf"'

        return response

    except Exception as e:
        return HttpResponse(str(e), status_code=500)
