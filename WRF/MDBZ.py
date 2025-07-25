from netCDF4 import Dataset
import matplotlib.pyplot as plt
import cartopy.crs as crs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature
from wrf import (to_np,interplevel, getvar, get_cartopy, cartopy_xlim, cartopy_ylim, latlon_coords)
import wrffuncs
from datetime import datetime
from metpy.plots import ctables
import pandas as pd

"""
Plot of the simulated composite reflectivty ('mdbz') with/without wind barbs
"""

# --- USER INPUT ---
wrf_date_time = datetime(2022,11,17,19,35,00)
domain = 2

windbarbs = False

SIMULATION = 1 # If comparing runs
path = f"/data2/white/WRF_OUTPUTS/PROJ_LEE/ELEC_IOP_2/ATTEMPT_{SIMULATION}/"
savepath = f"/data2/white/PLOTS_FIGURES/PROJ_LEE/ELEC_IOP_2/ATTEMPT_{SIMULATION}/"

# --- END USER INPUT ---

# Build/Find the time data for the model runs
time_df = wrffuncs.build_time_df(path, domain)
obs_time = pd.to_datetime(wrf_date_time)

# Compute absolute time difference
closest_idx = (time_df["time"] - obs_time).abs().argmin()

# Extract the matched row
match = time_df.iloc[closest_idx]

# Unpack matched file info
matched_file = match["filename"]
matched_timeidx = match["timeidx"]
matched_time = match["time"]

print(f"Closest match: {matched_time} in file {matched_file} at time index {matched_timeidx}")

with Dataset(matched_file) as ds:
    # Get the maxiumum reflectivity and convert units
    mdbz = getvar(ds, "mdbz", timeidx=matched_timeidx)
    ua  = getvar(ds, "ua", units="kt", timeidx=matched_timeidx)
    va = getvar(ds, "va", units="kt",timeidx=matched_timeidx)
    p = getvar(ds, "pressure",timeidx=matched_timeidx)
    u_500 = interplevel(ua, p, 900)
    v_500 = interplevel(va, p, 900)

# Get the latitude and longitude points
lats, lons = latlon_coords(mdbz)

# Get the cartopy mapping object
cart_proj = get_cartopy(mdbz)

# Create a figure
fig = plt.figure(figsize=(30,15))
# Set the GeoAxes to the projection used by WRF
ax = plt.axes(projection=cart_proj)

# Download and add the states, lakes and coastlines
states = NaturalEarthFeature(category="cultural", scale="50m", facecolor="none", name="admin_1_states_provinces")
ax.add_feature(states, linewidth=.1, edgecolor="black")
ax.add_feature(cfeature.LAKES.with_scale('50m'),linewidth=1, facecolor="none",  edgecolor="black")
ax.coastlines('50m', linewidth=1)

levels = [10, 15, 20, 25, 30, 35, 40, 45,50,55,60]

nwscmap = ctables.registry.get_colortable('NWSReflectivity')

# Make the filled countours with specified levels and range
qcs = plt.contourf(to_np(lons), to_np(lats),mdbz,levels=levels,transform=crs.PlateCarree(),cmap=nwscmap)

# Add a color bar
cbar = plt.colorbar()
cbar.set_label("dBZ",fontsize=10)

# Set the map bounds
ax.set_xlim(cartopy_xlim(mdbz))
ax.set_ylim(cartopy_ylim(mdbz))

# Add the gridlines
gl = ax.gridlines(color="black", linestyle="dotted",draw_labels=True, x_inline=False, y_inline=False)
gl.xlabel_style = {'rotation': 'horizontal','size': 14,'ha':'center'} # Change 14 to your desired font size
gl.ylabel_style = {'size': 14}  # Change 14 to your desired font size
gl.xlines = True
gl.ylines = True

gl.top_labels = False  # Disable top labels
gl.right_labels = False  # Disable right labels
gl.xpadding = 20


# Add the 500 hPa wind barbs, only plotting every 125th data point.
if windbarbs == True:
	plt.barbs(to_np(lons[::25,::25]), to_np(lats[::25,::25]),
          to_np(u_500[::25, ::25]), to_np(v_500[::25, ::25]),
          transform=crs.PlateCarree(), length=6)

#Adjust format for date to use in figure
date_format = wrf_date_time.strftime("%Y-%m-%d %H:%M:%S")
plt.title(f"Simulated Composite Reflectivty (dBZ) at {date_format}",fontsize="14")

# Filename friendly (No colons or spaces)
time_str = matched_time.strftime("%Y-%m-%d_%H-%M-%S")
# Use in filename
filename = f"4castLES_{time_str}.png"

plt.savefig(savepath+filename)

plt.show()
