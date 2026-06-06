import os
from huggingface_hub import hf_hub_download

def download_gemma():
    repo_id = "google/gemma-3-1b-it-GGUF"
    filename = "gemma-3-1b-it-Q4_K_M.gguf"
    local_dir = "models"
    
    # Asegurar que el directorio existe
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
        print(f"Directorio '{local_dir}' creado.")

    local_path = os.path.join(local_dir, filename)
    
    if os.path.exists(local_path):
        print(f"El modelo ya existe en: {local_path}")
        return

    print(f"Descargando {filename} desde {repo_id}...")
    try:
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        print(f"Descarga completada: {local_path}")
    except Exception as e:
        print(f"Error al descargar el modelo: {e}")
        print("\nIntenta instalar la librería necesaria si no la tienes:")
        print("pip install huggingface_hub")

if __name__ == "__main__":
    download_gemma()
