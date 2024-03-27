import streamlit as st
import boto3
import time
from botocore.exceptions import NoCredentialsError

# Inicialización del cliente de S3
s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = 'docdigi'

def upload_file_to_s3(file):
    try:
        # Sube el archivo al bucket en la carpeta input-document
        s3_client.upload_fileobj(file, bucket_name, f'input-document/{file.name}')
        return True
    except NoCredentialsError:
        return False

def check_file_in_output(file_name, wait_time=420, interval=30):
    """Espera hasta que el archivo aparezca en la carpeta output o se agote el tiempo de espera."""
    start_time = time.time()
    while time.time() - start_time < wait_time:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f'output/{file_name}')
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'] == f'output/{file_name}':
                    return True
        time.sleep(interval)
    return False

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name, 'Key': object_name},
                                                    ExpiresIn=expiration)
        return response
    except Exception as e:
        st.error(f"Error al generar URL presignada: {e}")
        return None

# Interfaz de Streamlit
st.title('Cargador y Procesador de Documentos S3')

uploaded_file = st.file_uploader("Elige un archivo para subir a S3")
if uploaded_file is not None:
    if upload_file_to_s3(uploaded_file):
        st.success('Archivo cargado exitosamente. Esperando procesamiento...')
        file_name = uploaded_file.name.split('.')[0] + '.pdf'  # Asume que el archivo de salida será .pdf
        if check_file_in_output(file_name):
            st.success('El archivo ha sido procesado y está listo para descargar.')
            download_url = generate_presigned_url(bucket_name, f'output/{file_name}')
            st.markdown(f"[Descargar archivo]({download_url})")
        else:
            st.error('El archivo no se ha generado en el tiempo esperado. Por favor, intenta de nuevo más tarde.')
    else:
        st.error('Error al cargar el archivo. Asegúrate de que las credenciales y permisos son correctos.')
