from os import path
import numpy as np
import math
from matplotlib import pyplot as plt
from lightkurve import search_lightcurve

import json
from pathlib import Path

class ExoplanetPipeline():
    """
    JOANUS: Automated Exoplanet Detection & Characterization Pipeline.
    Designed for Survey Data (Kepler, TESS, Roman Space Telescope).
    """

    def __init__(self, target_object="Kepler-10", quarter="02", fallback_sun_radius=1.000):
        self.target_object = target_object
        self.mission = "Kepler"
        self.quarter = quarter
        self.sun_radius = fallback_sun_radius
        self.is_star_radius_estimated = True
        
        # Raw & Processed Lightcurve State
        self.downloaded_result = None
        self.periodogram = None
        self.folded_lc = None
        self.binned_lc = None
        
        # BLS Detections
        self.best_period = None
        self.best_t0 = None
        self.best_duration = None
        self.snr = None
        
        # Physical Attributes (Relative & Absolute)
        self.transit_depth = None
        self.transit_depth_in_ppm = None
        self.radius_ratio = None  # Rp / R* (Pure Photometric Metric)
        self.planet_radius_to_earth_radii = None
        self.planet_radius_kilometers = None

        # Validation State
        self.is_candidate_valid = False

    def download_and_clean(self):
        print(f"[{self.target_object}] Searching Lightcurve...")
        search_result = search_lightcurve(self.target_object, mission=self.mission, quarter=self.quarter)
        print(f"[{self.target_object}] Lightcurve found.")

        print(f"[{self.target_object}] Downloading Data Products...")
        raw_lc = search_result[0].download()

        # Step A: Stellar Radius Inspection (Metadata / Catalog Check)
        try:
            detected_radius = float(raw_lc.meta['RADIUS'])
            if not math.isnan(detected_radius) and detected_radius > 0:
                self.sun_radius = detected_radius
                self.is_star_radius_estimated = False
                print(f"[{self.target_object}] Catalog Star Radius detected: {self.sun_radius:.3f} R☉")
            else:
                raise ValueError("Radius is NaN or non-physical.")
        except (KeyError, AttributeError, ValueError, TypeError):
            print(f"[{self.target_object}] Catalog metadata missing. Fallback Star Radius: {self.sun_radius:.3f} R☉ (Estimated=True)")

        # Step B: Data Ingestion & Cleaning
        self.downloaded_result = (
            raw_lc
            .remove_nans()
            .remove_outliers(sigma=5)
            .normalize()
            .flatten(window_length=101)
        )
        print(f"[{self.target_object}] Result downloaded & cleaned.")

    def run_bls(self, min_period=0.5, max_period=5.0):
        durations = np.linspace(0.05, 0.15, 10)
        print(f"[{self.target_object}] Running Box Least Squares (BLS) Periodogram...")
        
        self.periodogram = self.downloaded_result.to_periodogram(
            method='bls',
            minimum_period=min_period,
            maximum_period=max_period,
            frequency_factor=400.0,
            duration=durations
        )
        
        self.best_period = self.periodogram.period_at_max_power
        self.best_t0 = self.periodogram.transit_time_at_max_power
        self.best_duration = self.periodogram.duration_at_max_power

        print(f"!!!-> Best Period:    {self.best_period}")
        print(f"!!!-> Exact T0:       {self.best_t0}")
        print(f"!!!-> Duration:       {self.best_duration}")

        # Signal-to-Noise Ratio (SNR)
        power_max = self.periodogram.max_power.value
        power_std = np.std(self.periodogram.power.value)
        self.snr = float(power_max / power_std)

        print(f"[{self.target_object}] Signal-to-Noise Ratio (SNR): {self.snr:.2f}")

        if self.snr < 5.0:
            print(f"[{self.target_object}] ⚠️ WARNING: Low SNR (< 5.0). Signal might be noise!")

    def fold_data(self):
        print(f"[{self.target_object}] Phase Folding Light Curve at P = {self.best_period.value:.4f} d...")
        self.folded_lc = self.downloaded_result.fold(period=self.best_period, epoch_time=self.best_t0)
        self.binned_lc = self.folded_lc.bin(time_bin_size=0.01)
        print(f"[{self.target_object}] Data Folded and Binned.")

    def plot_bls(self):
        print(f"[{self.target_object}] Exporting Periodogram Plot...")
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        self.periodogram.plot(ax=ax1)
        ax1.set_title(f"{self.target_object} - BLS Periodogram (Peak: {self.best_period.value:.4f} d)")

        path_periodogram = path.abspath(f"data/{self.target_object.lower()}_bls_periodogram.png")
        plt.savefig(path_periodogram)
        plt.close(fig1)

    def plot_auto(self):
        print(f"[{self.target_object}] Exporting Phase Folded Transit Plot...")
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        self.folded_lc.plot(ax=ax2, alpha=0.2, c='grey', label="Raw Folded")
        self.binned_lc.plot(ax=ax2, c="red", lw=2, label="Binned Transit")

        ax2.set_ylim(0.998, 1.002)
        ax2.axhline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.7, label='Baseline (1.000)')
        ax2.set_title(f"{self.target_object} - Autonomously Detected Transit (P = {self.best_period.value:.4f} d)")

        path_transit = path.abspath(f"data/{self.target_object.lower()}_detected_transit.png")
        plt.savefig(path_transit)
        plt.close(fig2)


    def compute_physics(self):
        print(f"[{self.target_object}] Computing Physical Metrics...")
        min_flux = float(np.min(self.binned_lc.flux.value))
        self.transit_depth = 1.0 - min_flux
        self.transit_depth_in_ppm = self.transit_depth * 1_000_000

        # Relatives Radienverhältnis (Rp / R*)
        self.radius_ratio = math.sqrt(self.transit_depth)

        # Physikalische Radien
        planet_radius_solar = self.sun_radius * self.radius_ratio
        self.planet_radius_to_earth_radii = planet_radius_solar * 109.2
        self.planet_radius_kilometers = 6371 * self.planet_radius_to_earth_radii

        print(f"\n--- PHYSICAL RESULTS ({self.target_object}) ---")
        print(f"Transit Depth (δ):          {self.transit_depth_in_ppm:.2f} ppm")
        print(f"Radius Ratio (R_p / R_*):   {self.radius_ratio:.5f}")
        print(f"Star Radius Used:           {self.sun_radius:.3f} R☉ (Estimated={self.is_star_radius_estimated})")
        print(f"Calculated Planet Radius:   {self.planet_radius_to_earth_radii:.2f} R⊕")
        print(f"Calculated Planet Radius:   {self.planet_radius_kilometers:,.0f} Km\n")

        # Validation Suite direkt nach der Physik-Berechnung ausführen
        self.validate_signal()
        
    def validate_signal(self):
        print(f"[{self.target_object}] Running Validation Suite (False Positive Checks)...")
        
        # 1. Odd/Even Depth Check (Eclipsing Binary Filter)
        even_mask = np.arange(len(self.folded_lc)) % 2 == 0
        odd_mask = ~even_mask
        
        lc_even = self.folded_lc[even_mask].bin(time_bin_size=0.01)
        lc_odd = self.folded_lc[odd_mask].bin(time_bin_size=0.01)
        
        depth_even = 1.0 - float(np.min(lc_even.flux.value))
        depth_odd = 1.0 - float(np.min(lc_odd.flux.value))
        
        max_depth = max(depth_even, depth_odd)
        depth_diff_ratio = abs(depth_even - depth_odd) / max_depth if max_depth > 0 else 0.0
        
        odd_even_pass = depth_diff_ratio < 0.15
        print(f"-> Odd/Even Mismatch: {depth_diff_ratio * 100:.2f}% (Pass: {odd_even_pass})")

        # 2. Secondary Eclipse Check (Phase 0.4 - 0.6)
        phase_values = self.binned_lc.phase.value
        secondary_mask = (phase_values >= 0.4) & (phase_values <= 0.6)
        
        if np.any(secondary_mask):
            sec_min_flux = float(np.min(self.binned_lc.flux.value[secondary_mask]))
            sec_depth = 1.0 - sec_min_flux
            secondary_pass = sec_depth < (self.transit_depth * 0.30)
        else:
            secondary_pass = True
            
        print(f"-> Secondary Eclipse Check: Pass = {secondary_pass}")

        # Final Evaluation
        self.is_candidate_valid = odd_even_pass and secondary_pass and (self.snr >= 5.0)
        
        if self.is_candidate_valid:
            print(f"✓ VALIDATION SUCCESS: {self.target_object} passed all planet checks!\n")
        else:
            print(f"⚠️ VALIDATION FAILED: {self.target_object} flagged as potential False Positive!\n")

    def save_results(self):
        data = {
            "target": self.target_object,
            "quarter": self.quarter,
            "period_days": float(self.best_period.value),
            "snr": float(self.snr),
            "transit_depth_ppm": float(self.transit_depth_in_ppm),
            "radius_ratio_rp_rs": float(self.radius_ratio),
            "star_radius_solar": float(self.sun_radius),
            "is_star_radius_estimated": self.is_star_radius_estimated,
            "planet_radius_earth": float(self.planet_radius_to_earth_radii),
            "planet_radius_km": float(self.planet_radius_kilometers),
            "is_valid_candidate": self.is_candidate_valid
        }
        
        out_path = Path(f"data/{self.target_object.lower()}_results.json")
        out_path.parent.mkdir(exist_ok=True)
        
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        print(f"[{self.target_object}] JSON metadata exported to {out_path}")