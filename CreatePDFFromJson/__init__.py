from jinja2 import Template
import base64
import os
import tempfile
import logging
import pyodbc
from azure.functions import HttpRequest, HttpResponse
from weasyprint import HTML
from azure.storage.blob import BlobServiceClient

def main(req: HttpRequest) -> HttpResponse:
    #try:
        data = req.get_json()
        api_key = req.params.get('code')


        if not data:

            return HttpResponse("JSON data not provided", status_code=400)

        logging.info(data)

        #Henter Logo:
        # Get the Azure Storage connection string from environment variables
        connection_string = os.environ["Vet365Storage"]

        # Assume that the logo blob name is provided in the 'logo_blob_name' field of the data dictionary
        clinic_data = get_clinic_data(api_key)

        # Henter Logo URL:
        logo_blob_name = clinic_data.ConsultationLogoUrl

        #henter Templatename:
        template_name = clinic_data.ConsultationTemplateName

        # Sjekk om det er en logo_blob_name
        if logo_blob_name:
            # Get the image blob data from Azure Blob Storage
            image_data = get_blob_data(connection_string, "vet365", logo_blob_name)

            # Encode the image data to Base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Legg til den Base64-kodede bildedataen i data-dictionaryet
            data['logo_base64'] = image_base64
        else:
            # Hvis det ikke er noen logo_blob_name, sett logo_base64 til en tom streng
            data['logo_base64'] = ''
            #Henting logo slutt

        # Les HTML-templaten
        with open(template_name, "r") as template_file:
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

    ##except Exception as e:
        #return HttpResponse(str(e), status_code=500)
    

def get_blob_data(connection_string, container_name, blob_name):
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        # Download the blob data
        blob_data = blob_client.download_blob().readall()

        return blob_data

def get_clinic_data(api_key):
        
    # Koble til SQL-databasen
    connection = pyodbc.connect(os.environ["SqlConnectionString"])

    # Opprett en SQL-kursor
    cursor = connection.cursor()

    # Utfør SQL-spørringen for å hente data (endre spørringen etter dine behov)
    query = "SELECT ConsultationLogoUrl,ConsultationTemplateName FROM dbo.Clinics WHERE ApiKey = ?"  # Endret spørringen for å hente kun logo_url
    cursor.execute(query, api_key)

    # Hent resultatene
    result = cursor.fetchone()


    # Lukk tilkoblingen
    connection.close()

    if result:
        # Extract the logo_url value
        logging.info(f"Result from SQL Query: {result}")
        return result
    else:
        logging.warning("No data found for the given API key.")
        return None