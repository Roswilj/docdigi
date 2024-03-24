import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError

# Configuración inicial de Boto3 S3
s3_client = boto3.client('s3')
bucket_name = 'docdigi'

def upload_file_to_s3(file):
    """Sube un archivo al S3 y lo copia a otra carpeta dentro del mismo bucket."""
    try:
        s3_client.upload_fileobj(file, bucket_name, f'input-document/{file.name}')
        s3_client.copy_object(Bucket=bucket_name,
                              CopySource={'Bucket': bucket_name, 'Key': f'input-document/{file.name}'},
                              Key=f'output/{file.name}')
        return True
    except NoCredentialsError:
        return False

def list_files_in_output():
    """Lista los archivos en la carpeta 'output' de S3."""
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='output/')
    files = [item['Key'] for item in response.get('Contents', []) if item['Key'] != 'output/']
    return files

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Genera una URL presignada para descargar archivos de S3."""
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

# Barra lateral con opciones
with st.sidebar:
    st.header("Configuraciones")
    procesar_inmediatamente = st.checkbox("Procesar archivo inmediatamente después de cargar", value=True)

# Tabs para la aplicación
tab1, tab2 = st.tabs(["Carga de Archivo", "Visualización de Archivos"])

with tab1:
    # Cargador de archivos
    uploaded_file = st.file_uploader("Elige un archivo para subir a S3", key="file_uploader")
    if uploaded_file is not None and procesar_inmediatamente:
        if upload_file_to_s3(uploaded_file):
            st.success('Archivo cargado y procesado exitosamente.')
        else:
            st.error('Error al cargar el archivo. Asegúrate de que las credenciales y permisos son correctos.')

with tab2:
    st.header("Archivos Procesados en S3")
    files = list_files_in_output()
    if files:
        for file_path in files:
            file_name = file_path.split('/')[-1]  # Extrae solo el nombre del archivo
            download_url = generate_presigned_url(bucket_name, file_path)
            if download_url:
                st.markdown(f"{file_name}: [Descargar]({download_url})")
    else:
        st.write("No hay archivos procesados para mostrar.")
