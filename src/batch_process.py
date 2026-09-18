import csv
import time
import concurrent.futures
from pathlib import Path
from pipeline import ExoplanetPipeline

# Funktion, die für JEDEN Stern auf einem eigenen CPU-Kern ausgeführt wird
def process_single_target(target_info):
    name = target_info["target"]
    quarter = target_info["quarter"]
    
    print(f"[Core] Starting {name}...")
    try:
        pipeline = ExoplanetPipeline(target_object=name, quarter=quarter)
        pipeline.download_and_clean()
        pipeline.run_bls()
        pipeline.fold_data()
        pipeline.plot_bls()
        pipeline.plot_auto()
        pipeline.compute_physics()
        
        status_str = "VALID" if pipeline.is_candidate_valid else "FLAGGED"
        
        return {
            "target": name,
            "status": status_str,
            "period": f"{pipeline.best_period.value:.4f} d",
            "radius_earth": f"{pipeline.planet_radius_to_earth_radii:.2f} R⊕",
            "snr": f"{pipeline.snr:.1f}"
        }

    except Exception as e:
        return {
            "target": name,
            "status": "ERROR",
            "period": "N/A",
            "radius_earth": "N/A",
            "snr": "N/A",
            "error_msg": str(e)
        }

def run_parallel_batch(csv_file="targets.csv"):
    targets = []
    
    # 1. Daten aus CSV einlesen
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets.append(row)

    print(f"=== STARTING JOANUS PARALLEL BATCH ({len(targets)} targets) ===\n")
    start_time = time.time()
    summary_results = []

    # 2. Multiprocessing Pool starten (nutzt alle verfügbaren CPU-Kerne)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Map verteilt die Liste der Targets an die CPU-Kerne
        results = executor.map(process_single_target, targets)
        
        for res in results:
            summary_results.append(res)

    end_time = time.time()
    
    # 3. Summary ausgeben
    print("\n=================== BATCH EXECUTION SUMMARY ===================")
    print(f"{'Target':<12} | {'Status':<8} | {'SNR':<6} | {'Period':<10} | {'Radius':<10}")
    print("-" * 60)
    for res in summary_results:
        print(f"{res['target']:<12} | {res['status']:<8} | {res['snr']:<6} | {res['period']:<10} | {res['radius_earth']:<10}")
    print("===============================================================")
    print(f"Total Processing Time: {end_time - start_time:.2f} seconds\n")

if __name__ == "__main__":
    run_parallel_batch()