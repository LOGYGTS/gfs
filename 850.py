import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm

# GFS dosya klasörü
data_dir = r"C:\Users\proxd\Desktop\masado\modeldeneme\gfs_data"
files = sorted([f for f in os.listdir(data_dir) if f.endswith(".grib2")])

# Dosya isimlerinden tarih ve saat çıkar
file_info = []
for f in files:
    parts = f.split('_')
    date_str = parts[1]          
    hour_str = parts[2][1:4]     
    base_date = datetime.strptime(date_str, "%Y%m%d")
    forecast_hour = int(hour_str)
    forecast_time = base_date + timedelta(hours=forecast_hour)
    file_info.append((f, forecast_time))

root = tk.Tk()
root.title("850hPa Sıcaklık")

fig, ax = plt.subplots(figsize=(12,8), subplot_kw={'projection': ccrs.PlateCarree()})
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

cbar = None

# Aralıklar ve renkler
bounds = list(range(-40, 42, 2))  # -40 → 40 2°C aralık
colors = []
for b in bounds[:-1]:
    if b < -10:
        # -40 → -10 pembe → mor → beyaz
        frac = (b + 40)/30  # -40 -> -10
        r = int(255*(1-frac) + 255*frac)
        g = int(192*frac)
        bcol = int(203*(1-frac) + 255*frac)
        colors.append(f'#{r:02x}{g:02x}{bcol:02x}')
    elif -10 <= b <= 0:
        # -10 → 0 mavi tonları
        frac = (b + 10)/10  # -10->0
        r = int(69 + frac*(69-69))   # sabit 69
        g = int(117 + frac*(117-117)) # sabit 117
        bcol = int(180 + frac*(180-255))  # koyulaşacak mavi
        colors.append(f'#{r:02x}{g:02x}{bcol:02x}')
    elif 0 < b <= 10:
        # 0 → 10 yeşil → turuncu
        frac = (b-0)/10
        r = int(145 + frac*(254-145))
        g = int(207 + frac*(224-207))
        bcol = int(96 + frac*(139-96))
        colors.append(f'#{r:02x}{g:02x}{bcol:02x}')
    else:
        # 10 → 40 kırmızı tonları
        frac = (b-10)/30
        r = int(165 + frac*(165-165))
        g = int(0 + frac*(0-0))
        bcol = int(38 + frac*(38-38))
        colors.append(f'#{r:02x}{g:02x}{bcol:02x}')

cmap = LinearSegmentedColormap.from_list('custom_temp', colors)
norm = BoundaryNorm(bounds, cmap.N)

def plot_hour(idx):
    global cbar
    ax.clear()
    file_name, forecast_time = file_info[idx]
    file_path = os.path.join(data_dir, file_name)
    try:
        ds = xr.open_dataset(file_path, engine="cfgrib",
                             filter_by_keys={'typeOfLevel':'isobaricInhPa','level':850},
                             backend_kwargs={'indexpath':''})
    except Exception as e:
        print("Hata:", e)
        return

    t = ds['t'] - 273.15
    lons = ds.longitude.values
    lats = ds.latitude.values
    lon2d, lat2d = np.meshgrid(lons, lats)

    ax.set_extent([-20, 50, 25, 60], crs=ccrs.PlateCarree())  # Avrupa + Türkiye geniş
    ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='whitesmoke')
    ax.add_feature(cfeature.OCEAN.with_scale('10m'), facecolor='lightblue')
    ax.add_feature(cfeature.LAKES.with_scale('10m'), facecolor='lightblue')
    ax.add_feature(cfeature.RIVERS.with_scale('10m'))
    ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1)
    ax.add_feature(cfeature.BORDERS.with_scale('10m'), linestyle=':')

    im = ax.pcolormesh(lon2d, lat2d, t.values, cmap=cmap, norm=norm, shading='auto', transform=ccrs.PlateCarree())

    if cbar is None:
        cbar = fig.colorbar(im, ax=ax, orientation='vertical', fraction=0.03, pad=0.04, label='°C')
    else:
        cbar.update_normal(im)

    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size':10}
    gl.ylabel_style = {'size':10}

    ax.set_title(f"850 hPa Sıcaklık (°C)\nTahmin: {forecast_time.strftime('%Y-%m-%d %H:%M UTC')}", fontsize=14, fontweight='bold')
    canvas.draw()

slider = ttk.Scale(root, from_=0, to=len(files)-1, orient=tk.HORIZONTAL,
                   command=lambda val: plot_hour(int(float(val))))
slider.pack(fill=tk.X, padx=10, pady=10)

plot_hour(0)
root.mainloop()
