import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster, HeatMap
import numpy as np
import os


# ============================
# ŚCIEŻKI DO PLIKÓW
# ============================
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
TICKETS_GEO_FILE = os.path.join(DATA_DIR, "tickets_with_geo.xlsx")
AGG_FILE = os.path.join(DATA_DIR, "tickets_by_gmina.xlsx")


# ============================
# ŁADOWANIE DANYCH
# ============================
@st.cache_data
def load_data():
    df = pd.read_excel(TICKETS_GEO_FILE)
    df_agg = pd.read_excel(AGG_FILE)

    # konwersja dat
    df["Created At"] = pd.to_datetime(df["Created At"])
    df["Resolved At"] = pd.to_datetime(df["Resolved At"])
    df["Deadline"] = pd.to_datetime(df["Deadline"])

    # metryki czasowe bazowe
    df["Resolution_Time"] = df["Resolved At"] - df["Created At"]
    df["Resolution_Hours"] = df["Resolution_Time"].dt.total_seconds() / 3600
    df["SLA_Met"] = df["Resolved At"] <= df["Deadline"]

    # --- KONWERSJA NOWYCH METRYK CZASOWYCH (HH:MM:SS → godziny) ---
    time_cols = ["Total RT", "Elapsed RT", "Total Work Time"]
    for col in time_cols:
        if col in df.columns:
            df[col] = pd.to_timedelta(df[col], errors="coerce")
            df[col] = df[col].dt.total_seconds() / 3600  # zamiana na godziny (float)

    # Service Performance Overdued = 0/1
    if "Service Performance Overdued" in df.columns:
        df["Service Performance Overdued"] = pd.to_numeric(
            df["Service Performance Overdued"], errors="coerce"
        )

    return df, df_agg


# ============================
# KPI — SLA / MTTR / MTBF
# ============================
def compute_kpi(df):
    df = df.copy()

    if df.empty:
        return {
            "MTTR": 0.0,
            "SLA_MET_PCT": 0.0,
            "AVG_DEADLINE_PCT": 0.0,
            "MTBF": 0.0
        }

    mttr = df["Resolution_Hours"].mean()
    sla_met_pct = df["SLA_Met"].mean() * 100
    avg_deadline_pct = df["Deadline %"].mean()

    df_sorted = df.sort_values("Created At")
    df_sorted["Time_Between"] = df_sorted["Created At"].diff().dt.total_seconds() / 3600
    mtbf = df_sorted["Time_Between"].mean()

    return {
        "MTTR": mttr,
        "SLA_MET_PCT": sla_met_pct,
        "AVG_DEADLINE_PCT": avg_deadline_pct,
        "MTBF": mtbf
    }


# ============================
# MAPA PUNKTOWA
# ============================
def build_point_map(df):
    df_valid = df.dropna(subset=["lat", "lon"])
    if df_valid.empty:
        return None

    center_lat = df_valid["lat"].astype(float).mean()
    center_lon = df_valid["lon"].astype(float).mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
    cluster = MarkerCluster().add_to(m)

    counts = (
        df_valid.groupby("Gmina")
        .size()
        .reset_index(name="Liczba_ticketów")
    )
    df_merged = df_valid.merge(counts, on="Gmina", how="left")

    def get_color(count):
        if count >= 50:
            return "red"
        elif count >= 20:
            return "orange"
        else:
            return "green"

    for _, row in df_merged.iterrows():
        color = get_color(row["Liczba_ticketów"])
        popup_text = (
            f"<b>Gmina:</b> {row['Gmina']}<br>"
            f"<b>Powiat:</b> {row['Powiat']}<br>"
            f"<b>Województwo:</b> {row['Województwo']}<br>"
            f"<b>Liczba ticketów:</b> {row['Liczba_ticketów']}"
        )

        folium.CircleMarker(
            location=[float(row["lat"]), float(row["lon"])],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=popup_text
        ).add_to(cluster)

    return m


# ============================
# HEATMAPA
# ============================
def build_heatmap(df):
    df_valid = df.dropna(subset=["lat", "lon"])
    if df_valid.empty:
        return None

    center_lat = df_valid["lat"].astype(float).mean()
    center_lon = df_valid["lon"].astype(float).mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
    heat_data = df_valid[["lat", "lon"]].astype(float).values.tolist()
    HeatMap(heat_data, radius=15, blur=20, max_zoom=12).add_to(m)
    return m


# ============================
# GŁÓWNY DASHBOARD
# ============================
def main():
    st.set_page_config(page_title="ITSM Tickets Dashboard", layout="wide")

    st.title("ITSM Tickets — Geo, SLA, Technicy, Root Cause")

    df, df_agg = load_data()

    # --------------------------
    # FILTRY PODSTAWOWE
    # --------------------------
    st.sidebar.header("Filtry podstawowe")

    wojew_filter = st.sidebar.selectbox(
        "Województwo",
        options=["(wszystkie)"] + sorted(df["Województwo"].dropna().unique().tolist())
    )

    powiat_filter = st.sidebar.selectbox(
        "Powiat",
        options=["(wszystkie)"] + sorted(df["Powiat"].dropna().unique().tolist())
    )

    category_filter = st.sidebar.multiselect(
        "Kategoria (Category)",
        options=sorted(df["Category"].dropna().unique().tolist()),
        default=[]
    )

    client_filter = st.sidebar.multiselect(
        "Klient (Client)",
        options=sorted(df["Client"].dropna().unique().tolist()),
        default=[]
    )

    resolved_by_filter = st.sidebar.multiselect(
        "Technik (Resolved By)",
        options=sorted(df["Resolved By"].dropna().unique().tolist()),
        default=[]
    )

    root_cause_filter = st.sidebar.multiselect(
        "Root Cause",
        options=sorted(df["Root Cause"].dropna().unique().tolist()),
        default=[]
    )

    # --------------------------
    # FILTRY ZAAWANSOWANE
    # --------------------------
    st.sidebar.header("Filtry zaawansowane — SLA / czas")

    min_date = df["Created At"].min().date()
    max_date = df["Created At"].max().date()

    date_range = st.sidebar.date_input(
        "Zakres dat (Created At)",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    sla_breached_only = st.sidebar.checkbox("Tylko tickety z przekroczonym SLA", value=False)

    max_resolution_hours = float(df["Resolution_Hours"].max())
    resolution_hours_max_filter = st.sidebar.slider(
        "Maksymalny czas rozwiązania (h)",
        min_value=0.0,
        max_value=max_resolution_hours,
        value=max_resolution_hours,
        step=1.0
    )

    deadline_pct_min = st.sidebar.slider(
        "Minimalny Deadline % (wykorzystanie SLA)",
        min_value=0,
        max_value=100,
        value=0,
        step=5
    )

    # --------------------------
    # ZASTOSOWANIE FILTRÓW
    # --------------------------
    df_filtered = df.copy()

    if wojew_filter != "(wszystkie)":
        df_filtered = df_filtered[df_filtered["Województwo"] == wojew_filter]
    if powiat_filter != "(wszystkie)":
        df_filtered = df_filtered[df_filtered["Powiat"] == powiat_filter]

    if category_filter:
        df_filtered = df_filtered[df_filtered["Category"].isin(category_filter)]

    if client_filter:
        df_filtered = df_filtered[df_filtered["Client"].isin(client_filter)]

    if resolved_by_filter:
        df_filtered = df_filtered[df_filtered["Resolved By"].isin(resolved_by_filter)]

    if root_cause_filter:
        df_filtered = df_filtered[df_filtered["Root Cause"].isin(root_cause_filter)]

    df_filtered = df_filtered[
        (df_filtered["Created At"].dt.date >= start_date) &
        (df_filtered["Created At"].dt.date <= end_date)
    ]

    df_filtered = df_filtered[
        df_filtered["Resolution_Hours"] <= resolution_hours_max_filter
    ]

    df_filtered = df_filtered[
        df_filtered["Deadline %"] >= deadline_pct_min
    ]

    if sla_breached_only:
        df_filtered = df_filtered[df_filtered["SLA_Met"] == False]

    # --------------------------
    # KPI — SLA / MTTR / MTBF
    # --------------------------
    st.markdown("### KPI — SLA / MTTR / MTBF")

    kpi = compute_kpi(df_filtered)

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)

    with col_k1:
        st.metric("MTTR (h)", round(kpi["MTTR"], 2))

    with col_k2:
        st.metric("SLA Met (%)", f"{kpi['SLA_MET_PCT']:.1f}%")

    with col_k3:
        st.metric("Średni Deadline %", f"{kpi['AVG_DEADLINE_PCT']:.1f}%")

    with col_k4:
        st.metric("MTBF (h)", round(kpi["MTBF"], 2))

    # --------------------------
    # PERFORMANCE METRICS
    # --------------------------
    st.markdown("### Performance Metrics — RT / SLA / Work Time")

    perf_cols = [
        "Total RT",
        "Elapsed RT",
        "Service Performance Overdued",
        "Total Work Time"
    ]

    if all(col in df_filtered.columns for col in perf_cols) and not df_filtered.empty:
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)

        avg_total_rt = df_filtered["Total RT"].mean()
        avg_elapsed_rt = df_filtered["Elapsed RT"].mean()
        overdued_pct = df_filtered["Service Performance Overdued"].mean() * 100
        avg_work_time = df_filtered["Total Work Time"].mean()

        with col_p1:
            st.metric("Średni Total RT (h)", f"{avg_total_rt:.2f}")

        with col_p2:
            st.metric("Średni Elapsed RT (SLA h)", f"{avg_elapsed_rt:.2f}")

        with col_p3:
            st.metric("Overdued (%)", f"{overdued_pct:.1f}%")

        with col_p4:
            st.metric("Średni Total Work Time (h)", f"{avg_work_time:.2f}")

        st.markdown("#### Performance per Technik (Resolved By)")
        tech_perf = df_filtered.groupby("Resolved By").agg(
            Tickets=("Resolved By", "count"),
            Avg_Total_RT=("Total RT", "mean"),
            Avg_Elapsed_RT=("Elapsed RT", "mean"),
            Avg_Work_Time=("Total Work Time", "mean"),
            Overdued_Pct=("Service Performance Overdued", lambda x: x.mean() * 100)
        ).sort_values("Tickets", ascending=False)
        st.dataframe(tech_perf)

        st.markdown("#### Performance per Root Cause")
        rc_perf = df_filtered.groupby("Root Cause").agg(
            Tickets=("Root Cause", "count"),
            Avg_Total_RT=("Total RT", "mean"),
            Avg_Elapsed_RT=("Elapsed RT", "mean"),
            Avg_Work_Time=("Total Work Time", "mean"),
            Overdued_Pct=("Service Performance Overdued", lambda x: x.mean() * 100)
        ).sort_values("Tickets", ascending=False)
        st.dataframe(rc_perf)
    else:
        st.info("Brak kompletnych danych dla metryk: Total RT / Elapsed RT / Service Performance Overdued / Total Work Time.")

    # --------------------------
    # MAPY
    # --------------------------
    col_map1, col_map2 = st.columns(2)
    with col_map1:
        st.markdown("### Mapa punktowa (cluster + kolory)")
        m_points = build_point_map(df_filtered)
        if m_points:
            st_folium(m_points, width=700, height=500)
        else:
            st.info("Brak danych do wyświetlenia mapy punktowej.")

    with col_map2:
        st.markdown("### Heatmapa")
        m_heat = build_heatmap(df_filtered)
        if m_heat:
            st_folium(m_heat, width=700, height=500)
        else:
            st.info("Brak danych do wyświetlenia heatmapy.")

    # --------------------------
    # WYKRES TOP GMIN
    # --------------------------
    st.markdown("### TOP gmin z największą liczbą ticketów")

    df_agg_filtered = df_agg.copy()
    if wojew_filter != "(wszystkie)":
        df_agg_filtered = df_agg_filtered[df_agg_filtered["Województwo"] == wojew_filter]
    if powiat_filter != "(wszystkie)":
        df_agg_filtered = df_agg_filtered[df_agg_filtered["Powiat"] == powiat_filter]

    top_n = st.slider("TOP N gmin (wykres)", min_value=5, max_value=50, value=20, step=5)
    df_top = df_agg_filtered.head(top_n)

    if not df_top.empty:
        st.bar_chart(
            df_top.set_index("Gmina")["Liczba_ticketów"]
        )
    else:
        st.info("Brak danych do wyświetlenia wykresu.")

    # --------------------------
    # ANALIZA TECHNIKÓW
    # --------------------------
    st.markdown("### Analiza techników (Resolved By)")

    if not df_filtered.empty:
        tech_group = df_filtered.groupby("Resolved By").agg(
            Tickets=("Resolved By", "count"),
            MTTR=("Resolution_Hours", "mean"),
            SLA_Met_Pct=("SLA_Met", lambda x: x.mean() * 100)
        ).sort_values("Tickets", ascending=False)

        st.dataframe(tech_group)

        st.bar_chart(tech_group["Tickets"])
    else:
        st.info("Brak danych do analizy techników dla wybranych filtrów.")

    # --------------------------
    # ANALIZA ROOT CAUSE
    # --------------------------
    st.markdown("### Analiza Root Cause")

    if not df_filtered.empty:
        rc_group = df_filtered.groupby("Root Cause").agg(
            Tickets=("Root Cause", "count"),
            MTTR=("Resolution_Hours", "mean"),
            SLA_Met_Pct=("SLA_Met", lambda x: x.mean() * 100)
        ).sort_values("Tickets", ascending=False)

        st.dataframe(rc_group)

        st.bar_chart(rc_group["Tickets"])
    else:
        st.info("Brak danych do analizy Root Cause dla wybranych filtrów.")

    # --------------------------
    # TABELA TICKETÓW — WIDOK SZCZEGÓŁOWY
    # --------------------------
    st.markdown("### Widok ticketów — tabela z wyszukiwaniem")

    search_text = st.text_input(
        "Szukaj (Gmina, Powiat, Województwo, Category, Client, Resolved By, Root Cause):",
        ""
    )

    df_tickets_view = df_filtered.copy()

    if search_text:
        mask = (
            df_tickets_view["Gmina"].astype(str).str.contains(search_text, case=False, na=False) |
            df_tickets_view["Powiat"].astype(str).str.contains(search_text, case=False, na=False) |
            df_tickets_view["Województwo"].astype(str).str.contains(search_text, case=False, na=False) |
            df_tickets_view["Category"].astype(str).str.contains(search_text, case=False, na=False) |
            df_tickets_view["Client"].astype(str).str.contains(search_text, case=False, na=False) |
            df_tickets_view["Resolved By"].astype(str).str.contains(search_text, case=False, na=False) |
            df_tickets_view["Root Cause"].astype(str).str.contains(search_text, case=False, na=False)
        )
        df_tickets_view = df_tickets_view[mask]

    cols_to_show = [
        "Created At",
        "Resolved At",
        "Deadline",
        "Deadline %",
        "Resolution_Hours",
        "SLA_Met",
        "Total RT",
        "Elapsed RT",
        "Service Performance Overdued",
        "Total Work Time",
        "Category",
        "Client",
        "Resolved By",
        "Root Cause",
        "Gmina",
        "Powiat",
        "Województwo"
    ]
    existing_cols = [c for c in cols_to_show if c in df_tickets_view.columns]

    st.dataframe(df_tickets_view[existing_cols])

    # --------------------------
    # TABELA AGREGACJI
    # --------------------------
    st.markdown("### Tabela agregacji (gminy)")

    st.dataframe(df_agg_filtered)


if __name__ == "__main__":
    main()
