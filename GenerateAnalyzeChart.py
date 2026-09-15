import os
import glob
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# USTAWIENIA
# ==============================================================================
root_magisterka_dir = r"C:\Users\User\Downloads\Magisterka"
if not os.path.exists(root_magisterka_dir):
    print(f"[BŁĄD] Nie znaleziono katalogu: {root_magisterka_dir}")
    exit()
analysis_files = glob.glob(
    os.path.join(root_magisterka_dir, "**", "analysis_panel_*.xlsx"),
    recursive=True
)
print(f"[INFO] Liczba znalezionych plików: {len(analysis_files)}")
if not analysis_files:
    print("[BŁĄD] Nie znaleziono plików analysis_panel_*.xlsx.")
    exit()
# ==============================================================================
# 1. PRZYPISANIE GRUP BADAWCZYCH
# ==============================================================================

def classify_panel_group(folder_name):
    name = str(folder_name).lower().replace(" ", "").replace("_", "")
    # Najpierw sprawdzana jest grupa referencyjna, ponieważ nazwa "notdamaged" zawiera również "damaged".
    if "notdamaged" in name:
        return "Not_Damaged"
    if "damaged" in name:
        return "Damaged"
    if "poli" in name or "poly" in name:
        return "Poly"
    if "mono" in name:
        return "Mono"
    return "Other"
all_dfs = []
sns.set_theme(style="whitegrid")
# ==============================================================================
# 2. ODCZYT POSZCZEGÓLNYCH SERII I WYKRESY LOKALNE
# ==============================================================================
print("\n--- PRZETWARZANIE SERII POMIAROWYCH ---")
for file_path in analysis_files:
    # Pomijanie pliku zbiorczego
    if "MASTER_ANALYSIS_DATASET" in file_path:
        continue
    folder_name = os.path.basename(os.path.dirname(file_path))
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"[UWAGA] Nie udało się odczytać pliku: {file_path}")
        print(f"       Powód: {e}")
        continue
    group = classify_panel_group(folder_name)
    df["Panel_Group"] = group
    df["Source_Folder"] = folder_name
    # --------------------------------------------------------------------------
    # Konwersja wybranych kolumn na wartości liczbowe
    # --------------------------------------------------------------------------
    numeric_columns = [
        "Production_Wh",
        "Radiation_Global_Wm2",
        "T_Panel_Mean",
        "T_HOT_MAX",
        "Delta_T_HotSpot",
        "Wind_Speed_ms",
        "Temp_Ambient_C",
        "Humidity_pct"
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    all_dfs.append(df)
    # --------------------------------------------------------------------------
    # Wykresy dla pojedynczej serii pomiarowej
    # --------------------------------------------------------------------------
    try:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        plt.subplots_adjust(hspace=0.32, wspace=0.25)
        # ----------------------------------------------------------------------
        # 1. Produkcja energii a promieniowanie
        # ----------------------------------------------------------------------
        ax1 = axes[0, 0]
        data = df.dropna(
            subset=["Radiation_Global_Wm2", "Production_Wh"]
        )
        if not data.empty:
            scatter = ax1.scatter(
                data["Radiation_Global_Wm2"],
                data["Production_Wh"],
                c=data["Delta_T_HotSpot"],
                cmap="plasma",
                s=70,
                edgecolors="black"
            )
            plt.colorbar(
                scatter,
                ax=ax1,
                label="ΔT [°C]"
            )
            sns.regplot(
                data=data,
                x="Radiation_Global_Wm2",
                y="Production_Wh",
                ax=ax1,
                scatter=False,
                color="red"
            )
            ax1.set_title(
                f"Produkcja a promieniowanie – {folder_name}",
                fontsize=11,
                fontweight="bold"
            )
            ax1.set_xlabel("Promieniowanie [W/m²]")
            ax1.set_ylabel("Produkcja [Wh]")
        else:
            ax1.text(
                0.5,
                0.5,
                "Brak danych produkcji lub promieniowania",
                ha="center",
                va="center"
            )
        # ----------------------------------------------------------------------
        # 2. Różnica temperatury a średnia temperatura modułu
        # ----------------------------------------------------------------------
        ax2 = axes[0, 1]
        data = df.dropna(
            subset=["T_Panel_Mean", "Delta_T_HotSpot"]
        )
        if not data.empty:
            ax2.scatter(
                data["T_Panel_Mean"],
                data["Delta_T_HotSpot"],
                color="crimson",
                s=70,
                edgecolors="black"
            )
            sns.regplot(
                data=data,
                x="T_Panel_Mean",
                y="Delta_T_HotSpot",
                ax=ax2,
                scatter=False,
                color="darkred"
            )
            ax2.set_title(
                "ΔT hot spotu a średnia temperatura modułu",
                fontsize=11,
                fontweight="bold"
            )
            ax2.set_xlabel("Średnia temperatura modułu [°C]")
            ax2.set_ylabel("ΔT [°C]")
        else:
            ax2.text(
                0.5,
                0.5,
                "Brak danych temperaturowych",
                ha="center",
                va="center"
            )
        # ----------------------------------------------------------------------
        # 3. Różnica temperatury a prędkość wiatru
        # ----------------------------------------------------------------------
        ax3 = axes[1, 0]
        data = df.dropna(
            subset=["Wind_Speed_ms", "Delta_T_HotSpot"]
        )
        if not data.empty:
            ax3.scatter(
                data["Wind_Speed_ms"],
                data["Delta_T_HotSpot"],
                color="teal",
                s=70,
                edgecolors="black"
            )
            sns.regplot(
                data=data,
                x="Wind_Speed_ms",
                y="Delta_T_HotSpot",
                ax=ax3,
                scatter=False,
                color="darkgreen"
            )
            ax3.set_title(
                "ΔT hot spotu a prędkość wiatru",
                fontsize=11,
                fontweight="bold"
            )
            ax3.set_xlabel("Prędkość wiatru [m/s]")
            ax3.set_ylabel("ΔT [°C]")
        else:
            ax3.text(
                0.5,
                0.5,
                "Brak danych dotyczących wiatru",
                ha="center",
                va="center"
            )
        # ----------------------------------------------------------------------
        # 4. Macierz korelacji
        # ----------------------------------------------------------------------
        ax4 = axes[1, 1]
        correlation_columns = [
            "T_Panel_Mean",
            "T_HOT_MAX",
            "Delta_T_HotSpot",
            "Radiation_Global_Wm2",
            "Wind_Speed_ms",
            "Production_Wh"
        ]
        correlation_columns = [
            column
            for column in correlation_columns
            if column in df.columns
            and df[column].dropna().count() > 1
        ]
        if len(correlation_columns) >= 2:
            sns.heatmap(
                df[correlation_columns].corr(),
                annot=True,
                fmt=".2f",
                cmap="coolwarm",
                vmin=-1,
                vmax=1,
                ax=ax4
            )
            ax4.set_title(
                "Korelacje w pojedynczej serii",
                fontsize=11,
                fontweight="bold"
            )
            ax4.tick_params(axis="x", rotation=30)
        else:
            ax4.text(
                0.5,
                0.5,
                "Zbyt mało danych do obliczenia korelacji",
                ha="center",
                va="center"
            )
        # ----------------------------------------------------------------------
        # Zapis wykresu
        # ----------------------------------------------------------------------
        dashboard_path = os.path.splitext(file_path)[0] + "_dashboard.png"
        plt.savefig(
            dashboard_path,
            dpi=180,
            bbox_inches="tight"
        )
        plt.close()
        print(
            f" -> Wykres: {os.path.basename(dashboard_path)} "
            f"(grupa: {group})"
        )
    except Exception as e:
        print(f"[UWAGA] Problem podczas tworzenia wykresu: {e}")
# ==============================================================================
# 3. UTWORZENIE BAZY ZBIORCZEJ
# ==============================================================================
if not all_dfs:
    print("[BŁĄD] Nie udało się wczytać żadnego pliku.")
    exit()
master_df = pd.concat(
    all_dfs,
    ignore_index=True
)
# ==============================================================================
# 4. KLASYFIKACJA HOT SPOTÓW
# ==============================================================================
def classify_iec(delta_t):
    if pd.isna(delta_t):
        return np.nan
    if delta_t < 10.0:
        return "Class 1 (<10°C - Minor)"
    if delta_t < 20.0:
        return "Class 2 (10-20°C - Medium)"
    return "Class 3 (>=20°C - Critical)"
master_df["IEC_Class"] = (
    master_df["Delta_T_HotSpot"].apply(classify_iec)
)
# ==============================================================================
# 5. NORMALIZACJA PRODUKCJI WZGLĘDEM PROMIENIOWANIA
# ==============================================================================
master_df["Yield_per_Irradiance"] = np.where(
    master_df["Radiation_Global_Wm2"] > 20,
    master_df["Production_Wh"] /
    master_df["Radiation_Global_Wm2"],
    np.nan
)
# ==============================================================================
# 6. ZAPIS BAZY I TABEL STATYSTYCZNYCH
# ==============================================================================
output_master = os.path.join(
    root_magisterka_dir,
    "MASTER_ANALYSIS_DATASET.xlsx"
)
master_df.to_excel(
    output_master,
    index=False
)
summary_excel = os.path.join(
    root_magisterka_dir,
    "summary_thesis_tables.xlsx"
)
with pd.ExcelWriter(summary_excel) as writer:
    # Statystyki według grup badawczych
    (
        master_df
        .groupby("Panel_Group")
        .agg({
            "Delta_T_HotSpot": ["count", "mean", "std", "max"],
            "T_Panel_Mean": ["mean", "min", "max"],
            "Production_Wh": ["count", "mean", "std"]
        })
        .round(2)
        .to_excel(
            writer,
            sheet_name="By_Group"
        )
    )
    # Statystyki według klasy hot spotu
    (
        master_df
        .groupby("IEC_Class")
        .agg({
            "Delta_T_HotSpot": ["count", "mean", "max"],
            "Production_Wh": ["count", "mean", "std"]
        })
        .round(2)
        .to_excel(
            writer,
            sheet_name="By_IEC_Class"
        )
    )
    # Zestawienie grup badawczych i klas
    pd.crosstab(
        master_df["Panel_Group"],
        master_df["IEC_Class"]
    ).to_excel(
        writer,
        sheet_name="Group_x_IEC"
    )
print(f"\n[SUKCES] Baza zbiorcza: {output_master}")
print(f"[SUKCES] Tabele statystyczne: {summary_excel}")
# ==============================================================================
# 7. WYKRESY ZBIORCZE DO PRACY
# ==============================================================================
print("\n--- GENEROWANIE WYKRESÓW ZBIORCZYCH ---")
sns.set_theme(
    style="whitegrid",
    font_scale=1.1
)
# ==============================================================================
# RYSUNEK 1 – DAMAGED VS NOT_DAMAGED
# ==============================================================================
df_pair = master_df[
    master_df["Panel_Group"].isin(["Damaged", "Not_Damaged"])
].dropna(
    subset=["Radiation_Global_Wm2", "Production_Wh"]
)
if not df_pair.empty:
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=df_pair,
        x="Radiation_Global_Wm2",
        y="Production_Wh",
        hue="Panel_Group",
        style="Panel_Group",
        palette={
            "Damaged": "#e74c3c",
            "Not_Damaged": "#27ae60"
        },
        s=85,
        alpha=0.85
    )
    damaged = df_pair[
        df_pair["Panel_Group"] == "Damaged"
    ]
    reference = df_pair[
        df_pair["Panel_Group"] == "Not_Damaged"
    ]
    if not damaged.empty:
        sns.regplot(
            data=damaged,
            x="Radiation_Global_Wm2",
            y="Production_Wh",
            scatter=False,
            color="#c0392b",
            line_kws={
                "label": "Trend: Damaged (Opt 1.1.13)"
            }
        )
    if not reference.empty:
        sns.regplot(
            data=reference,
            x="Radiation_Global_Wm2",
            y="Production_Wh",
            scatter=False,
            color="#219653",
            line_kws={
                "label": "Trend: Not Damaged (Opt 1.1.15)"
            }
        )
    plt.title(
        "Produkcja energii a promieniowanie – moduł uszkodzony i referencyjny",
        fontsize=13,
        fontweight="bold"
    )
    plt.xlabel("Promieniowanie całkowite [W/m²]")
    plt.ylabel("Produkcja energii [Wh]")
    plt.legend()
    fig1_path = os.path.join(
        root_magisterka_dir,
        "fig1_comparative_production_regression.png"
    )
    plt.savefig(
        fig1_path,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()
    print(f" -> Wykres 1: {fig1_path}")
# ==============================================================================
# RYSUNEK 2 – ROZKŁAD ΔT I KLASYFIKACJA
# ==============================================================================
plt.figure(figsize=(13, 5))
plt.subplot(1, 2, 1)
sns.boxplot(
    data=master_df,
    x="Panel_Group",
    y="Delta_T_HotSpot",
    hue="Panel_Group",
    palette={
        "Damaged": "#e74c3c",
        "Not_Damaged": "#2ecc71",
        "Mono": "#3498db",
        "Poly": "#9b59b6"
    },
    legend=False
)
plt.title(
    "Rozkład ΔT hot spotów w grupach badawczych",
    fontweight="bold"
)
plt.ylabel("ΔT [°C]")
plt.xlabel("Grupa badawcza")
plt.subplot(1, 2, 2)
iec_classes = [
    "Class 1 (<10°C - Minor)",
    "Class 2 (10-20°C - Medium)",
    "Class 3 (>=20°C - Critical)"
]
present_classes = [
    class_name
    for class_name in iec_classes
    if class_name in master_df["IEC_Class"].values
]
sns.countplot(
    data=master_df,
    x="IEC_Class",
    order=present_classes,
    hue="IEC_Class",
    palette="YlOrRd",
    legend=False
)
plt.title(
    "Klasyfikacja ΔT hot spotów wg IEC TS 62446-3",
    fontweight="bold"
)
plt.xlabel("Klasa")
plt.ylabel("Liczba obserwacji")
plt.xticks(rotation=20)
fig2_path = os.path.join(
    root_magisterka_dir,
    "fig2_hotspot_distribution_and_iec.png"
)
plt.savefig(
    fig2_path,
    dpi=300,
    bbox_inches="tight"
)
plt.close()
print(f" -> Wykres 2: {fig2_path}")
# ==============================================================================
# RYSUNEK 3 – ODPOWIEDŹ TEMPERATUROWA MONO VS POLY
# ==============================================================================
df_tech = master_df[
    master_df["Panel_Group"].isin(["Mono", "Poly"])
].dropna(
    subset=["T_Panel_Mean", "Yield_per_Irradiance"]
)
if not df_tech.empty:
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=df_tech,
        x="T_Panel_Mean",
        y="Yield_per_Irradiance",
        hue="Panel_Group",
        palette={
            "Mono": "#2980b9",
            "Poly": "#8e44ad"
        },
        alpha=0.75,
        s=70
    )
    mono = df_tech[
        df_tech["Panel_Group"] == "Mono"
    ]
    poly = df_tech[
        df_tech["Panel_Group"] == "Poly"
    ]
    if not mono.empty:
        sns.regplot(
            data=mono,
            x="T_Panel_Mean",
            y="Yield_per_Irradiance",
            scatter=False,
            color="#1f618d",
            line_kws={
                "label": "Trend: Monokrystaliczny"
            }
        )
    if not poly.empty:
        sns.regplot(
            data=poly,
            x="T_Panel_Mean",
            y="Yield_per_Irradiance",
            scatter=False,
            color="#6c3483",
            line_kws={
                "label": "Trend: Polikrystaliczny"
            }
        )
    plt.title(
        "Odpowiedź temperaturowa modułów Mono i Poly",
        fontsize=13,
        fontweight="bold"
    )
    plt.xlabel("Średnia temperatura panelu [°C]")
    plt.ylabel("Znormalizowana produkcja [Wh / (W/m²)]")
    plt.legend()
    fig3_path = os.path.join(
        root_magisterka_dir,
        "fig3_thermal_degradation_trend.png"
    )
    plt.savefig(
        fig3_path,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()
    print(f" -> Wykres 3: {fig3_path}")
# ==============================================================================
# RYSUNEK 4 – ZBIORCZA MACIERZ KORELACJI
# ==============================================================================
correlation_columns = [
    "Production_Wh",
    "Yield_per_Irradiance",
    "Delta_T_HotSpot",
    "T_HOT_MAX",
    "T_Panel_Mean",
    "Radiation_Global_Wm2",
    "Temp_Ambient_C",
    "Wind_Speed_ms",
    "Humidity_pct"
]
correlation_columns = [
    column
    for column in correlation_columns
    if column in master_df.columns
    and master_df[column].dropna().count() > 1
]
if len(correlation_columns) >= 2:
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        master_df[correlation_columns].corr(),
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        linewidths=0.5
    )
    plt.title(
        "Macierz korelacji zmiennych w zbiorze danych",
        fontsize=13,
        fontweight="bold"
    )
    plt.xticks(
        rotation=35,
        ha="right"
    )
    fig4_path = os.path.join(
        root_magisterka_dir,
        "fig4_master_correlation_heatmap.png"
    )
    plt.savefig(
        fig4_path,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()
    print(f" -> Wykres 4: {fig4_path}")
print("\n[ZAKOŃCZONO] Przetwarzanie danych i generowanie wykresów zakończone.")

