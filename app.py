import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Inicialización del cliente de S3
s3_client = boto3.client('s3', region_name='us-east-1')
s3_client = boto3.client('s3')
bucket_name = 'docdigi-1'

def upload_file_to_s3(file):
    try:
        # Sube el archivo al bucket en la carpeta lang_pro
        s3_client.upload_fileobj(file, bucket_name, f'lang_pro/{file.name}')
        return True
    except NoCredentialsError:
        return False

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

    # Crea un objeto canvas de ReportLab para generar el PDF
    pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Escribe el contenido del archivo en el PDF
    text_lines = file_content.split('\n')
    y = 750
    for line in text_lines:
        pdf_canvas.drawString(100, y, line)
        y -= 20

    # Finaliza el PDF
    pdf_canvas.showPage()
    pdf_canvas.save()

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

# Cargador de archivos
uploaded_file = st.file_uploader("Elige un archivo para cargar y procesar")
if uploaded_file is not None:
    if upload_file_to_s3(uploaded_file):
        st.success('Archivo cargado exitosamente.')
    else:
        st.error('Error al cargar el archivo. Asegúrate de que las credenciales y permisos son correctos.')

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
