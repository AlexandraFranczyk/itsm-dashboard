import pandas as pd
import matplotlib.pyplot as plt

def plot_top_gminy(df, top_n=20, output="../data/top_gminy.png"):
    """
    Tworzy wykres TOP N gmin z największą liczbą ticketów.
    """
    df_top = df.head(top_n)

    plt.figure(figsize=(12, 8))
    plt.barh(df_top["Gmina"], df_top["Liczba_ticketów"], color="steelblue")
    plt.gca().invert_yaxis()  # największe na górze

    plt.title(f"TOP {top_n} gmin z największą liczbą ticketów")
    plt.xlabel("Liczba ticketów")
    plt.ylabel("Gmina")

    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()

    print(f"✔ Wykres zapisany jako: {output}")
