from os import path
import numpy as np
from matplotlib import pyplot as plt
from lightkurve import search_lightcurve

# 1. DATA INGESTION & CLEANUP
print("\nSearching Light Curve...")
target_object = "Kepler-10"
target_result = search_lightcurve(target_object, mission="Kepler", quarter="02")

print("Downloading and cleaning data...")
downloaded_result = (
    target_result[0]
    .download()
    .remove_nans()
    .remove_outliers(sigma=5)
    .normalize()
    .flatten(window_length=101)
)

# 2. BLS-ALGORITHM
print("Getting Box Least Squares...")
durations = np.linspace(0.05, 0.15, 10)
periodogram = downloaded_result.to_periodogram(
    method='bls',
    minimum_period=0.5,
    maximum_period=5.0,
    frequency_factor=200.0,
    duration=durations
)

# 3. PLANET PARAMETER EXTRAHIEREN
print("Reading Best Periodic Signal...")
best_period = periodogram.period_at_max_power
best_t0 = periodogram.transit_time_at_max_power
best_duration = periodogram.duration_at_max_power

print(f"-> Best Period:    {best_period}")
print(f"-> Exact T0:       {best_t0}")
print(f"-> Duration:       {best_duration}")

# 4. DYNAMIC PHASE FOLDING
print("Folding Data dynamically with detected parameters...")
folded_lc = downloaded_result.fold(period=best_period, epoch_time=best_t0)
binned_lc = folded_lc.bin(time_bin_size=0.01)

# 5. PLOT 1: BLS Periodogramm
print("Plotting BLS Periodogram...")
fig1, ax1 = plt.subplots(figsize=(10, 5))
periodogram.plot(ax=ax1)
ax1.set_title(f"BLS Periodogram - Peak at {best_period.value:.4f} days")

path_periodogram = path.abspath("data/kepler10_bls_periodogram.png")
plt.savefig(path_periodogram)
plt.close(fig1)

# 6. PLOT 2: Autonomically detected Transit
print("Plotting Detected Transit...")
fig2, ax2 = plt.subplots(figsize=(10, 5))
folded_lc.plot(ax=ax2, alpha=0.2, c='grey', label="Raw Folded")
binned_lc.plot(ax=ax2, c="red", lw=2, label="Binned Transit")

ax2.set_ylim(0.998, 1.002)
ax2.axhline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.7, label='Baseline (1.000)')
ax2.set_title(f"Autonomically found Transit (P = {best_period.value:.4f} d)")

path_transit = path.abspath("data/kepler10_detected_transit.png")
plt.savefig(path_transit)
plt.close(fig2)

print("\Succesfully went trough Pipeline!")
print(f"Periodogram: {path_periodogram}")
print(f"Transit Plot: {path_transit}")