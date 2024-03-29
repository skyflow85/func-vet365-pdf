import os
import tempfile
from azure.functions import HttpRequest, HttpResponse
from weasyprint import HTML
from datetime import datetime

def main(req: HttpRequest) -> HttpResponse:
    try:
        # Mottar HTML-innhold fra forespørselen
        html_content = req.get_body().decode('utf-8')

        # Hent gjeldende dato og klokkeslett
        now = datetime.now()
        formatted_datetime = now.strftime("%d.%m.%y %H:%M")

        # Legg til CSS-stykket for sidetall i @page i HTML-malen og angi skrifttypen og hvit bakgrunn
        html_content_with_header_footer = f'''

        <!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            /* margin box at top right showing page number */
            @top-right {{
                content: "Page " counter(pageNumber);
            }}
        }}
        body {{
            margin: 0;
            padding: 0;
            background-color: #fff; /* Hvit bakgrunn */
            font-family: Arial, sans-serif; /* Bruk Arial-skrifttypen eller en annen sans-serif-skrittype etter behov */
        }}
        .page {{
            position: relative;
            width: 100%;
            height: 100%;
        }}
        .page-header {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            text-align: right;
            font-size: 12px;
        }}
        .page-footer {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 12px;
        }}
        .main-content {{
            font-size: 10px; /* Change the font size for the main content to 14px */
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="page-header">
            Dato: {formatted_datetime}
        </div>
        <div class="main-content">
            {html_content}
        </div>
        <div class="page-footer">
            Page <span class="page-number"></span>
        </div>
    </div>
</body>
</html>
        '''

        # Opprett midlertidig fil for HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_html_file:
            tmp_html_file.write(html_content_with_header_footer.encode('utf-8'))
            tmp_html_file_name = tmp_html_file.name

        # Opprett midlertidig fil for PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf_file:
            tmp_pdf_file_name = tmp_pdf_file.name

        # Konverter HTML til PDF ved hjelp av WeasyPrint
        HTML(filename=tmp_html_file_name).write_pdf(tmp_pdf_file_name)

        # Les PDF-filen og send den som respons
        with open(tmp_pdf_file_name, 'rb') as pdf_file:
            pdf_content = pdf_file.read()

        os.remove(tmp_html_file_name)  # Slett midlertidig HTML-fil
        os.remove(tmp_pdf_file_name)   # Slett midlertidig PDF-fil

        return HttpResponse(pdf_content, mimetype='application/pdf', status_code=200)

    except Exception as e:
        return HttpResponse(f'Feil: {str(e)}', status_code=500)
