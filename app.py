import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError
from io import BytesIO
from PyPDF2 import PdfWriter, PdfReader

# Inicialización del cliente de S3
s3_client = boto3.client('s3', region_name='us-east-1')
s3_client = boto3.client('s3')
bucket_name = 'docdigi-1'

def get_latest_file_in_lang_pro():
    # Obtiene el archivo más reciente en la carpeta lang_pro
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='lang_pro/')
    files = [item['Key'] for item in response.get('Contents', []) if item['Key'] != 'lang_pro/']
    if files:
        latest_file = max(files, key=lambda x: s3_client.head_object(Bucket=bucket_name, Key=x)['LastModified'])
        return latest_file
    else:
        return None

def convert_to_pdf_and_save(latest_file):
    # Descarga el archivo más reciente de lang_pro
    file_obj = s3_client.get_object(Bucket=bucket_name, Key=latest_file)
    file_content = file_obj['Body'].read().decode('utf-8')

    # Crea un objeto BytesIO para almacenar el contenido del PDF en memoria
    pdf_buffer = BytesIO()

    # Crea un objeto PdfWriter de PyPDF2
    pdf_writer = PdfWriter()

    # Crea un objeto PdfReader a partir del contenido del archivo
    pdf_reader = PdfReader(BytesIO(file_content.encode('utf-8')))

    # Agrega las páginas del archivo al PdfWriter
    for page in range(len(pdf_reader.pages)):
        pdf_writer.add_page(pdf_reader.pages[page])

    # Escribe el contenido del PdfWriter en el BytesIO
    pdf_writer.write(pdf_buffer)

    # Mueve el puntero al inicio del BytesIO
    pdf_buffer.seek(0)

    # Genera el nombre del archivo de salida
    output_file_key = 'final_doc/' + latest_file.split('/')[-1].split('.')[0] + '.pdf'

    # Guarda el PDF en el bucket de S3 en la carpeta final_doc
    s3_client.put_object(Bucket=bucket_name, Key=output_file_key, Body=pdf_buffer)

    return output_file_key

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Genera una URL presignada para descargar archivos. Expira en 1 hora (3600 segundos) por defecto."""
    try:
        response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)
    except Exception as e:
        print(e)
        return None
    return response

# Título de la aplicación
st.title('Convertidor de Documentos a PDF')

# Obtiene el archivo más reciente de lang_pro
latest_file = get_latest_file_in_lang_pro()

if latest_file:
    # Convierte el archivo a PDF y lo guarda en final_doc
    output_file_key = convert_to_pdf_and_save(latest_file)

    # Genera un enlace presignado para la descarga
    download_url = generate_presigned_url(bucket_name, output_file_key)

    st.write(f"Archivo más reciente convertido a PDF:")
    st.write(f"Nombre del archivo: {output_file_key.split('/')[-1]}")
    st.write(f"Enlace de descarga: {download_url}")
else:
    st.write("No se encontraron archivos en la carpeta lang_pro.")
