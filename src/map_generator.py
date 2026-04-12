import folium
from folium.plugins import HeatMap, MarkerCluster
import pandas as pd


def generate_point_map(df, lat_col="lat", lon_col="lon", output="../data/map_points.html"):
    """
    Generuje mapę punktową z clusteringiem i kolorowaniem wg liczby ticketów.
    """

    df_valid = df.dropna(subset=[lat_col, lon_col])

    if df_valid.empty:
        print("❌ Brak danych GPS do wygenerowania mapy punktowej.")
        return

    # --- LICZENIE TICKETÓW NA GMINĘ ---
    counts = (
        df_valid.groupby("Gmina")
        .size()
        .reset_index(name="Liczba_ticketów")
    )

    df_merged = df_valid.merge(counts, on="Gmina", how="left")

    # --- USTALANIE KOLORÓW ---
    def get_color(count):
        if count >= 50:
            return "red"
        elif count >= 20:
            return "orange"
        else:
            return "green"

    center_lat = df_valid[lat_col].astype(float).mean()
    center_lon = df_valid[lon_col].astype(float).mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    cluster = MarkerCluster().add_to(m)

    # --- DODAWANIE PUNKTÓW ---
    for _, row in df_merged.iterrows():
        color = get_color(row["Liczba_ticketów"])

        popup_text = (
            f"<b>Gmina:</b> {row['Gmina']}<br>"
            f"<b>Powiat:</b> {row['Powiat']}<br>"
            f"<b>Województwo:</b> {row['Województwo']}<br>"
            f"<b>Liczba ticketów:</b> {row['Liczba_ticketów']}"
        )

        folium.CircleMarker(
            location=[float(row[lat_col]), float(row[lon_col])],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=popup_text
        ).add_to(cluster)

    m.save(output)
    print(f"✔ Mapa punktowa (kolor + cluster) zapisana jako: {output}")


def generate_heatmap(df, lat_col="lat", lon_col="lon", output="../data/map_heatmap.html"):
    """
    Generuje heatmapę na podstawie współrzędnych GPS.
    """
    df_valid = df.dropna(subset=[lat_col, lon_col])

    if df_valid.empty:
        print("❌ Brak danych GPS do wygenerowania heatmapy.")
        return

    center_lat = df_valid[lat_col].astype(float).mean()
    center_lon = df_valid[lon_col].astype(float).mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    heat_data = df_valid[[lat_col, lon_col]].astype(float).values.tolist()

    HeatMap(heat_data, radius=15, blur=20, max_zoom=12).add_to(m)

    m.save(output)
    print(f"✔ Heatmapa zapisana jako: {output}")
