import pandas as pd
import os

def load_tickets(path="../data/tickets.xlsx"):
    """
    Wczytuje plik tickets.xlsx i zwraca DataFrame.
    """
    full_path = os.path.join(os.path.dirname(__file__), path)

    try:
        df = pd.read_excel(full_path)
        print(f"Wczytano plik: {full_path}")
        return df
    except FileNotFoundError:
        print("❌ Nie znaleziono pliku tickets.xlsx w folderze /data")
        raise
    except Exception as e:
        print("❌ Błąd podczas wczytywania pliku:", e)
        raise
