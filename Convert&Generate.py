import os
import glob
import cv2
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import simpledialog

# Ustawienia
base_path = r"PathToDataFolder"
panel_width = 800
panel_height = 1200
display_height = 850
# Punkty kontrolne na zrektyfikowanym obrazie
control_points = {
    "P1": (100, 100),
    "P2": (400, 600),
    "P3": (700, 1100)
}
def pixel_to_temp(value, t_min, t_max):
    temperature = t_min + (value / 255.0) * (t_max - t_min)
    return round(temperature, 2)

def get_temperature_range():
    root = tk.Tk()
    root.withdraw()
    t_min = simpledialog.askfloat(
        "Skala temperatury",
        "Podaj dolną wartość skali [°C]:",
        initialvalue=9.0
    )
    t_max = simpledialog.askfloat(
        "Skala temperatury",
        "Podaj górną wartość skali [°C]:",
        initialvalue=25.0
    )
    root.destroy()
    return t_min, t_max

def process_image():
    global clicked_points
    global current_index
    global data_rows
    t_min, t_max = get_temperature_range()
    if t_min is None or t_max is None:
        print("Pominięto zdjęcie - nie podano zakresu temperatur.")
        move_to_next()
        return
    file_name = os.path.basename(images[current_index])
    points_src = np.float32(clicked_points) / scale_ratio
    points_dst = np.float32([
        [0, 0],
        [panel_width, 0],
        [panel_width, panel_height],
        [0, panel_height]
    ])
    transform = cv2.getPerspectiveTransform(points_src, points_dst)
    corrected = cv2.warpPerspective(
        original_image,
        transform,
        (panel_width, panel_height)
    )
    post_name = f"Post_Tmin{t_min}_Tmax{t_max}_{file_name}"
    post_path = os.path.join(output_folder_post, post_name)
    cv2.imwrite(post_path, corrected)
    gray = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)
    _, max_value, _, max_position = cv2.minMaxLoc(gray)
    hot_temperature = pixel_to_temp(max_value, t_min, t_max)
    analyzed = corrected.copy()
    point_temperatures = {}
    for name, point in control_points.items():
        x, y = point
        pixel_value = gray[y, x]
        temperature = pixel_to_temp(pixel_value, t_min, t_max)
        point_temperatures[f"T_{name}"] = temperature
        cv2.circle(analyzed, point, 6, (255, 0, 0), -1)
        cv2.putText(
            analyzed,
            f"{name}: {temperature} C",
            (x + 10, y + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            1
        )
    cv2.drawMarker(
        analyzed,
        max_position,
        (0, 0, 255),
        markerType=cv2.MARKER_CROSS,
        markerSize=30,
        thickness=2
    )
    cv2.putText(
        analyzed,
        f"HOT: {hot_temperature} C",
        (max_position[0] + 15, max_position[1] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2
    )
    analyzed_name = "Analyzed_" + post_name
    analyzed_path = os.path.join(output_folder_analyze, analyzed_name)
    cv2.imwrite(analyzed_path, analyzed)
    data_rows.append({
        "Plik": post_name,
        "T_min_skali": t_min,
        "T_max_skali": t_max,
        "T_P1": point_temperatures["T_P1"],
        "T_P2": point_temperatures["T_P2"],
        "T_P3": point_temperatures["T_P3"],
        "T_HOT_MAX": hot_temperature,
        "X_HOT": max_position[0],
        "Y_HOT": max_position[1]
    })
    print(
        f"[{current_index + 1}/{len(images)}] "
        f"{file_name} -> T_HOT_MAX = {hot_temperature} °C"
    )
    move_to_next()
def mouse_callback(event, x, y, flags, param):
    global clicked_points
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_points.append([x, y])
        cv2.circle(
            display_image,
            (x, y),
            8,
            (0, 255, 0),
            -1
        )
        cv2.imshow("Analiza termogramow", display_image)

        if len(clicked_points) == 4:
            process_image()
def move_to_next():
    global clicked_points
    global current_index
    clicked_points = []
    current_index += 1
    show_next_image()
def show_next_image():
    global original_image
    global display_image
    global scale_ratio
    if current_index >= len(images):
        cv2.destroyAllWindows()
        return
    original_image = cv2.imread(images[current_index])
    if original_image is None:
        print(
            f"Nie udało się odczytać pliku: "
            f"{os.path.basename(images[current_index])}"
        )
        move_to_next()
        return
    scale_ratio = display_height / original_image.shape[0]
    display_image = cv2.resize(
        original_image,
        (
            int(original_image.shape[1] * scale_ratio),
            display_height
        )
    )
    cv2.imshow("Analiza termogramow", display_image)
    cv2.setMouseCallback("Analiza termogramow", mouse_callback)
# Wybór katalogu z pomiarami
folders = [
    name for name in os.listdir(base_path)
    if os.path.isdir(os.path.join(base_path, name))
    and not name.endswith("Post")
    and not name.endswith("Analyze")
]
print("Dostępne foldery:")
for number, folder in enumerate(folders):
    print(f"{number}: {folder}")
folder_number = int(input("Wybierz numer folderu: "))
selected_folder = folders[folder_number]
input_folder = os.path.join(base_path, selected_folder)
output_folder_post = input_folder + "Post"
output_folder_analyze = output_folder_post + "Analyze"
os.makedirs(output_folder_post, exist_ok=True)
os.makedirs(output_folder_analyze, exist_ok=True)
excel_path = os.path.join(
    output_folder_analyze,
    "raport_final.xlsx"
)
# Wyszukiwanie zdjęć
images = []
for extension in ("*.bmp", "*.jpg", "*.jpeg"):
    images.extend(
        glob.glob(os.path.join(input_folder, extension))
    )
images.sort()
print(f"\nZnaleziono {len(images)} zdjęć.")
print(
    "Kliknij cztery narożniki panelu w kolejności: "
    "LG, PG, PD, LD."
)
print("S - pomiń zdjęcie, Q - zakończ program.")
# Zmienne robocze
current_index = 0
clicked_points = []
original_image = None
display_image = None
scale_ratio = 1.0
data_rows = []
# Uruchomienie okna podglądu
cv2.namedWindow("Analiza termogramow")
show_next_image()
while current_index < len(images):
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        print("\nPrzerwano działanie programu.")
        break
    if key == ord("s"):
        print(
            f"Pominięto: "
            f"{os.path.basename(images[current_index])}"
        )
        move_to_next()
cv2.destroyAllWindows()
# Zapis wyników
if data_rows:
    results = pd.DataFrame(data_rows)
    results.to_excel(excel_path, index=False)
    print(f"\nZapisano raport: {excel_path}")
else:
    print("\nNie ma danych do zapisania.")
