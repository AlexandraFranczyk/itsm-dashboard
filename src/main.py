from load_tickets import load_tickets
from geocode_api import geocode_location
from map_generator import generate_point_map, generate_heatmap
from aggregation import aggregate_by_gmina, save_aggregation_to_excel
from charts import plot_top_gminy
import pandas as pd


def main():
    # 1. Wczytanie danych
    df = load_tickets()

    # 2. Przygotowanie kolumn GPS
    df["lat"] = None
    df["lon"] = None

    print("Rozpoczynam geolokalizację ticketów...")

    # 3. Geolokalizacja każdego ticketu
    for i, row in df.iterrows():
        lat, lon = geocode_location(
            row["Gmina"],
            row["Powiat"],
            row["Województwo"]
        )
        df.at[i, "lat"] = lat
        df.at[i, "lon"] = lon

        print(f"{i+1}/{len(df)} → {row['Gmina']}, {row['Powiat']}, {row['Województwo']} → {lat}, {lon}")

    # 4. Zapis danych z GPS
    df.to_excel("../data/tickets_with_geo.xlsx", index=False)
    print("\n✔ Zapisano tickets_with_geo.xlsx")

    # 5. Generowanie map
    print("\nGeneruję mapę punktową...")
    generate_point_map(df)

    print("Generuję heatmapę...")
    generate_heatmap(df)

    # 6. Agregacja po gminach
    print("\nAgreguję dane po gminach...")
    agg = aggregate_by_gmina(df)
    save_aggregation_to_excel(agg)

    # 7. Wykres TOP 20 gmin
    print("\nTworzę wykres TOP 20 gmin...")
    plot_top_gminy(agg)

    print("\n✔ Gotowe! Mapa punktowa, heatmapa, agregacja i wykres zapisane w folderze /data")


if __name__ == "__main__":
    main()
