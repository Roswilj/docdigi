import streamlit as st
import boto3
import chardet
from botocore.exceptions import NoCredentialsError
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# Inicialización del cliente de S3
s3_client = boto3.client('s3', region_name='us-east-1')
s3_client = boto3.client('s3')
bucket_name = 'docdigi-1'


def upload_file_to_s3(file):
    try:
        # Sube el archivo al bucket en la carpeta input-document
        key = f'input-document/{file.name}'
        s3_client.upload_fileobj(file, bucket_name, key)
        return key  # Se devuelve el nombre clave del archivo subido
    except NoCredentialsError:
        return None


def get_latest_file_in_final_doc():
    # Obtiene el archivo más reciente en la carpeta final_doc
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='final_doc/')
    files = [item['Key'] for item in response.get('Contents', []) if item['Key'] != 'final_doc/']
    if files:
        latest_file = max(files, key=lambda x: s3_client.head_object(Bucket=bucket_name, Key=x)['LastModified'])
        return latest_file
    else:
        return None


def convert_to_pdf_and_save(latest_file, result=None):
    # Descarga el archivo más reciente de lang_pro
    file_obj = s3_client.get_object(Bucket=bucket_name, Key=latest_file)
    file_bytes = file_obj['Body'].read()

    # Detectar la codificación del archivo
    result = chardet.detect(file_bytes)
    encoding = result['encoding']

    # Si la codificación no se pudo detectar, se utiliza UTF-8 como predeterminada
    if encoding is None:
        encoding = 'utf-8'

    file_content = file_bytes.decode(encoding)

    # ... (el resto del código permanece igual) ...

    return output_file_key


def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Genera una URL presignada para descargar archivos. Expira en 1 hora (3600 segundos) por defecto."""
    try:
        response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(e)
        return None
    return response


# Título de la aplicación
st.title('Convertidor de Documentos a PDF')

# Cargador de archivos
uploaded_file = st.file_uploader("Elige un archivo para cargar y procesar")
if uploaded_file is not None:
    s3_key = upload_file_to_s3(uploaded_file)
    if s3_key:
        st.success('Archivo cargado exitosamente.')

        # Convierte el archivo cargado a PDF y lo guarda en final_doc
        output_file_key = convert_to_pdf_and_save(s3_key, {})  # Se pasa la clave del archivo subido a S3

        # Genera un enlace presignado para la descarga
        download_url = generate_presigned_url(bucket_name, output_file_key)

        st.write(f"Archivo convertido a PDF:")
        st.write(f"Nombre del archivo: {output_file_key.split('/')[-1]}")
        st.write(f"Enlace de descarga: {download_url}")
    else:
        st.error('Error al cargar el archivo. Asegúrate de que las credenciales y permisos son correctos.')

# Obtiene el archivo más reciente de final_doc
latest_file = get_latest_file_in_final_doc()

if latest_file:
    # Genera un enlace presignado para la descarga
    download_url = generate_presigned_url(bucket_name, latest_file)

    st.write(f"Archivo más reciente convertido a PDF:")
    st.write(f"Nombre del archivo: {latest_file.split('/')[-1]}")
    st.write(f"Enlace de descarga: {download_url}")
else:
    st.write("No se encontraron archivos en la carpeta final_doc.")
