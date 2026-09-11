print("Importing Packages...")
from lightkurve import search_lightcurve
from matplotlib import pyplot as plt
from os import path

print("\nSearching Light Curve...")
target_object = "Kepler-10"
target_result = search_lightcurve(target_object, mission="Kepler", quarter="02")

print("Downloading data...")
downloaded_result = target_result[0].download().remove_nans().remove_outliers(sigma=5).normalize().flatten(window_length=101)

print("Folding Data...")
folded_lc = downloaded_result.fold(period=0.8374, epoch_time=133.208)
binned_lc = folded_lc.bin(time_bin_size=0.01)

print("Plotting Data...")

ax = folded_lc.plot(alpha=0.2, c='grey', label="Raw Folded")
binned_lc.plot(ax=ax, c="red", lw=2, label="Binned Transit")
ax.set_ylim(0.998, 1.002)
ax.axhline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.7, label='Baseline (1.000)')


output_path = path.abspath("data/kepler10_transit_clean_plot.png")

print("Saving File...")
plt.savefig(output_path)
print(f"All Done! \033]8;;file://{output_path}\033\\Open File\033]8;;\033\\")
