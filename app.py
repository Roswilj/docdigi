import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError

# Inicialización del cliente de S3
s3_client = boto3.client('s3')
bucket_name = 'docdigi-1'

def upload_file_to_s3(file):
    try:
        # Sube el archivo al bucket en la carpeta input-document
        s3_client.upload_fileobj(file, bucket_name, f'input-document/{file.name}')
        # Copia el archivo desde input-document a output dentro del mismo bucket
        s3_client.copy_object(Bucket=bucket_name,
                              CopySource={'Bucket': bucket_name, 'Key': f'input-document/{file.name}'},
                              Key=f'output/{file.name}')
        return True
    except NoCredentialsError:
        return False

def list_files_in_output():
    # Obtiene una lista de los archivos en la carpeta output
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='output/')
    files = [item['Key'] for item in response.get('Contents', []) if item['Key'] != 'output/']
    return files

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Genera una URL presignada para descargar archivos. Expira en 1 hora (3600 segundos) por defecto."""
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(e)
        return None
    return response

# Título de la aplicación
st.title('Cargador y Procesador de Documentos S3')

# Cargador de archivos
uploaded_file = st.file_uploader("Elige un archivo para subir a S3")
if uploaded_file is not None:
    if upload_file_to_s3(uploaded_file):
        st.success('Archivo cargado y procesado exitosamente.')
    else:
        st.error('Error al cargar el archivo. Asegúrate de que las credenciales y permisos son correctos.')

# Listado de archivos procesados
st.header('Archivos Procesados en S3')
files = list_files_in_output()
if files:
    for file in files:
        file_name = file.split('/')[-1]  # Extrae solo el nombre del archivo
        # Genera un enlace presignado para la descarga
        download_url = generate_presigned_url(bucket_name, file)
        st.write(f"{file_name}: ", download_url)
else:
    st.write("No hay archivos procesados para mostrar.")
