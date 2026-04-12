import pandas as pd

def aggregate_by_gmina(df):
    """
    Zwraca tabelę: Gmina, Powiat, Województwo, Liczba ticketów
    """
    grouped = (
        df.groupby(["Gmina", "Powiat", "Województwo"])
        .size()
        .reset_index(name="Liczba_ticketów")
        .sort_values("Liczba_ticketów", ascending=False)
    )
    return grouped


def save_aggregation_to_excel(df, output="../data/tickets_by_gmina.xlsx"):
    df.to_excel(output, index=False)
    print(f"✔ Zapisano agregację do: {output}")
