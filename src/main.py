from pipeline import ExoplanetPipeline

if __name__ == "__main__":
    pipeline = ExoplanetPipeline()
    pipeline.download_and_clean()
    pipeline.run_bls()
    pipeline.fold_data()
    pipeline.plot_bls()
    pipeline.plot_auto()
    pipeline.compute_physics()
    pipeline.save_results()