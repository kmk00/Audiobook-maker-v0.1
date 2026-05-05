import os
import shutil

TEMP_AUDIO_DIR = "audiobooks/audio/temp"

def clear_temp_directory():
    """Funkcja, która upewnia się, że folder istnieje, a następnie usuwa tylko jego ZAWARTOŚĆ."""
    os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
    
    for filename in os.listdir(TEMP_AUDIO_DIR):
        file_path = os.path.join(TEMP_AUDIO_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path) 
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Nie udało się usunąć pliku {file_path}. Błąd: {e}")