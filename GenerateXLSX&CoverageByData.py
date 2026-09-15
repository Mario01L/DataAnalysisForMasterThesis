import os
import re
import datetime
import numpy as np
import pandas as pd

# Pliki wejściowe
path_meteo = r"C:\Users\User\Downloads\Magisterka\Weather\meteo 2025 wybrane dni.xlsx"
path_pv = r"C:\Users\User\Downloads\Magisterka\Weather\solaredge_C3_2025 1.xlsx"
sheet_name_meteo = "Results"
sheet_name_pv = "SE 2025"
# Sprawdzenie dostępności plików
if not os.path.exists(path_meteo):
    print(f"Nie znaleziono pliku meteorologicznego:\n{path_meteo}")
    raise SystemExit
if not os.path.exists(path_pv):
    print(f"Nie znaleziono pliku SolarEdge:\n{path_pv}")
    raise SystemExit
# Wybór katalogu z raportem termicznym
folder_input = input(
    "Podaj ścieżkę do katalogu Analyze: "
).strip().strip('"')
target_dir = os.path.abspath(folder_input)
path_raport = os.path.join(target_dir, "raport_final.xlsx")
if not os.path.exists(path_raport):
    print(f"Nie znaleziono pliku raportu:\n{path_raport}")
    raise SystemExit
# Wczytanie danych SolarEdge i wybór optymalizatora
df_pv_raw = pd.read_excel(
    path_pv,
    sheet_name=sheet_name_pv
)
optimizer_columns = [
    column
    for column in df_pv_raw.columns
    if "Optymalizator" in column
]
print("\nDostępne optymalizatory:")
for index, column in enumerate(optimizer_columns):
    match = re.search(
        r"Optymalizator\s+([\d\.]+)",
        column
    )
    optimizer_id = match.group(1) if match else column
    print(f"{index}: {optimizer_id}")
selected = input(
    "\nWybierz optymalizator (numer lub ID): "
).strip()
if selected.isdigit() and int(selected) < len(optimizer_columns):
    selected_column = optimizer_columns[int(selected)]
else:
    matches = [
        column
        for column in optimizer_columns
        if selected in column
    ]
    selected_column = (
        matches[0]
        if matches
        else optimizer_columns[0]
    )
optimizer_match = re.search(
    r"Optymalizator\s+([\d\.]+)",
    selected_column
)
optimizer_id = (
    optimizer_match.group(1)
    if optimizer_match
    else selected_column
)
print(f"Wybrano optymalizator: {optimizer_id}")
# Wczytanie raportu termograficznego
df_raport = pd.read_excel(path_raport)
def parse_filename_time(filename):
    text = str(filename)
    unix_match = re.search(
        r"_(\d{13})\.jpg",
        text
    )
    if unix_match:
        timestamp = int(unix_match.group(1)) / 1000
        return datetime.datetime.fromtimestamp(timestamp)
    xinf_match = re.search(
        r"Xinf_(\d{2})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})",
        text
    )
    if xinf_match:
        year, month, day, hour, minute, second = map(
            int,
            xinf_match.groups()
        )
        return datetime.datetime(
            2000 + year,
            month,
            day,
            hour,
            minute,
            second
        )
    return pd.NaT
df_raport["datetime"] = df_raport["Plik"].apply(
    parse_filename_time
)
df_raport = (
    df_raport
    .dropna(subset=["datetime"])
    .sort_values("datetime")
)
# Średnia temperatura modułu i różnica względem najcieplejszego punktu
temperature_columns = [
    "T_P1",
    "T_P2",
    "T_P3"
]
df_raport["T_Panel_Mean"] = (
    df_raport[temperature_columns]
    .mean(axis=1)
    .round(2)
)
df_raport["Delta_T_HotSpot"] = (
    df_raport["T_HOT_MAX"]
    - df_raport["T_Panel_Mean"]
).round(2)
df_raport["Optimizer_ID"] = optimizer_id
# Dane meteorologiczne
df_meteo_raw = pd.read_excel(
    path_meteo,
    sheet_name=sheet_name_meteo
)
data_meteo = df_meteo_raw.iloc[7:].copy()
data_meteo.columns = [
    "ID",
    "Date",
    "Time",
    "Radiation_Global_Wm2",
    "Pressure_hPa",
    "Humidity_pct",
    "Temp_Ambient_C",
    "Wind_Speed_ms",
    "Wind_Gust_ms",
    "Wind_Dir_deg",
    "Radiation_Diffuse_Wm2"
]
data_meteo = data_meteo.dropna(
    subset=["Date", "Time"]
)
def combine_meteo_datetime(row):
    date_value = row["Date"]
    time_value = row["Time"]
    if isinstance(
        date_value,
        (datetime.datetime, datetime.date)
    ):
        date_text = date_value.strftime("%Y-%m-%d")
    else:
        date_text = str(date_value).split(" ")[0]
    if isinstance(
        time_value,
        (datetime.datetime, datetime.time)
    ):
        time_text = time_value.strftime("%H:%M:%S")
    else:
        time_text = str(time_value)
    return pd.to_datetime(
        f"{date_text} {time_text}",
        errors="coerce"
    )
data_meteo["datetime"] = data_meteo.apply(
    combine_meteo_datetime,
    axis=1
)
data_meteo = (
    data_meteo
    .dropna(subset=["datetime"])
    .sort_values("datetime")
)
numeric_columns = [
    "Radiation_Global_Wm2",
    "Pressure_hPa",
    "Humidity_pct",
    "Temp_Ambient_C",
    "Wind_Speed_ms",
    "Radiation_Diffuse_Wm2"
]
for column in numeric_columns:
    data_meteo[column] = pd.to_numeric(
        data_meteo[column],
        errors="coerce"
    )
# Dane produkcyjne SolarEdge
def parse_pv_time(value):
    if pd.isna(value):
        return pd.NaT
    match = re.search(
        r"(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}:\d{2})",
        str(value)
    )
    if match:
        day, month, year, hour_minute = match.groups()

        return pd.to_datetime(
            f"{year}-{month}-{day} {hour_minute}:00"
        )
    return pd.to_datetime(
        value,
        errors="coerce"
    )
df_pv_raw["datetime"] = df_pv_raw.iloc[:, 0].apply(
    parse_pv_time
)
df_pv_clean = df_pv_raw[
    ["datetime", selected_column]
].copy()
df_pv_clean.columns = [
    "datetime",
    "Production_Wh"
]
df_pv_clean["Production_Wh"] = (
    df_pv_clean["Production_Wh"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)
df_pv_clean["Production_Wh"] = pd.to_numeric(
    df_pv_clean["Production_Wh"],
    errors="coerce"
)
df_pv_clean = df_pv_clean.sort_values(
    "datetime"
)
# Połączenie danych na podstawie znacznika czasu
meteo_columns = [
    "datetime",
    "Radiation_Global_Wm2",
    "Radiation_Diffuse_Wm2",
    "Temp_Ambient_C",
    "Wind_Speed_ms",
    "Humidity_pct"
]
merged_data = pd.merge_asof(
    df_raport,
    data_meteo[meteo_columns],
    on="datetime",
    direction="nearest",
    tolerance=pd.Timedelta("10min")
)
final_df = pd.merge_asof(
    merged_data.sort_values("datetime"),
    df_pv_clean,
    on="datetime",
    direction="nearest",
    tolerance=pd.Timedelta("35min")
)
# Zapis połączonego zbioru danych
output_path = os.path.join(
    target_dir,
    f"analysis_panel_opt_{optimizer_id}.xlsx"
)
final_df.to_excel(
    output_path,
    index=False
)
print(f"\nZapisano połączony zbiór danych:")
print(output_path)
print(f"Liczba rekordów: {len(final_df)}")
