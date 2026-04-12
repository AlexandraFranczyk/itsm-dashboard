import os
import shutil

# --- Nazwa głównego folderu projektu ---
BASE = os.path.dirname(os.path.abspath(__file__))

# --- Struktura folderów ---
folders = [
    "data",
    "src"
]

files = {
    "src/load_tickets.py": "",
    "src/geocode_api.py": "",
    "src/map_generator.py": "",
    "src/main.py": "",
    "requirements.txt": ""
}

def create_structure():
    print("Tworzę strukturę projektu...")

    # Tworzenie folderów
    for folder in folders:
        path = os.path.join(BASE, folder)
        os.makedirs(path, exist_ok=True)
        print(f"✔ Folder: {path}")

    # Tworzenie plików
    for file_path, content in files.items():
        full_path = os.path.join(BASE, file_path)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✔ Plik: {full_path}")

    print("\nStruktura projektu gotowa!")

if __name__ == "__main__":
    create_structure()
