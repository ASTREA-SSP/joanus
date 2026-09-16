import traceback
from pipeline import ExoplanetPipeline

TARGETS = [
    {"name": "Kepler-10", "quarter": "02"},
    {"name": "Kepler-8",  "quarter": "02"},
    {"name": "Kepler-22", "quarter": "02"},
]

def run_batch():
    summary_results = []

    print(f"=== STARTING JOANUS BATCH PROCESSING ({len(TARGETS)} targets) ===\n")

    for target in TARGETS:
        name = target["name"]
        quarter = target["quarter"]
        
        print(f"\n>>> PROCESSING: {name} (Quarter {quarter}) <<<")
        
        try:
            pipeline = ExoplanetPipeline(target_object=name, quarter=quarter)
            
            pipeline.download_and_clean()
            pipeline.run_bls()
            pipeline.fold_data()
            pipeline.plot_bls()
            pipeline.plot_auto()
            pipeline.compute_physics()  # Beinhaltet nun self.validate_signal()
            pipeline.save_results()
            
            status_str = "VALID" if pipeline.is_candidate_valid else "FLAGGED"
            
            summary_results.append({
                "target": name,
                "status": status_str,
                "period": f"{pipeline.best_period.value:.4f} d",
                "radius_earth": f"{pipeline.planet_radius_to_earth_radii:.2f} R⊕",
                "snr": f"{pipeline.snr:.1f}"
            })

        except Exception as e:
            print(f"❌ ERROR processing {name}: {e}")
            summary_results.append({
                "target": name,
                "status": "ERROR",
                "period": "N/A",
                "radius_earth": "N/A",
                "snr": "N/A"
            })

    print("\n=================== BATCH EXECUTION SUMMARY ===================")
    print(f"{'Target':<12} | {'Status':<8} | {'SNR':<6} | {'Period':<10} | {'Radius':<10}")
    print("-" * 60)
    for res in summary_results:
        print(f"{res['target']:<12} | {res['status']:<8} | {res['snr']:<6} | {res['period']:<10} | {res['radius_earth']:<10}")
    print("===============================================================\n")

if __name__ == "__main__":
    run_batch()