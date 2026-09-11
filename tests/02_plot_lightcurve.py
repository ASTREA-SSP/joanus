'''
1. IMPORT: 
   - Lade 'search_lightcurve' aus 'lightkurve'.
   - Lade 'matplotlib.pyplot' als 'plt'.

2. DATEN HOLEN & REINIGEN:
   - Suche nach Kepler-10 (Quarter 02).
   - Lade die Lichtkurve herunter (.download()).
   - Entferne ungültige Werte (NaNs) mit der Methode .remove_nans().

3. PLOTTEN (Zwei Ansichten vergleichen):
   - Methode A (Lightkurve-Standard): Nutze die eingebaute Funktion .plot(), um den Rohverlauf anzuzeigen.
   - Methode B (Gefaltete Lichtkurve / Phase Folding):
     - Kepler-10b hat eine sehr kurze Umlaufzeit (Period P ≈ 0.8374 Tage) und eine Transitzeit (t0 ≈ 133.2).
     - Nutze die Methode .fold(period=..., epoch_time=...), um alle Transits übereinanderzulegen.
     - Plotte die gefaltete Lichtkurve.

4. ANZEIGE / SPEICHERN:
   - Speichere die Graphik als Datei ab: plt.savefig("data/kepler10_transit.png")
'''
from lightkurve import search_lightcurve
from matplotlib import pyplot as plt
from os import path
from time import sleep

selected = None

while True:
   print("""
   Plot Methode angeben
   Methode A: Lightkurve Standard
   Methode B: Phase Folding
   """)

   selected = input("(A/B): > ").strip()

   if (selected in ("A", "a")):
      print(10*"\n"+"Methode A: Lightkurve Standard\n")
      break
   elif (selected in ("B", "b")):
      print(10*"\n"+"Methode B: Phase Folding\n")
      break
   else:
      print(10*"\n"+f"Angabe \"{selected}\" ist keine Korrekte Angabe.\n")
   sleep(1)

print("Searching Light Curve...")
target_object = "Kepler-10"
target_result = search_lightcurve(target_object, mission="Kepler", quarter="02")

print("Downloading data...")
downloaded_result = target_result[0].download().remove_nans()


if (selected in ("A", "a")): # Lightkurve Standard
   print("Saving Lightkurve Standard Plot...")
   downloaded_result.plot()
   
   output_path = path.abspath("data/kepler10_transit_lightkurve-standard.png")
   plt.savefig(output_path)
   print(f"All Done! \033]8;;file://{output_path}\033\\Open File\033]8;;\033\\")
else:
   print("Saving Phase Folding Plot...")
   folded_lc = downloaded_result.fold(period=0.8374, epoch_time=133.2)
   folded_lc.plot()

   output_path = path.abspath("data/kepler10_transit_phase-folding.png")
   plt.savefig(output_path)
   print(f"All Done! \033]8;;file://{output_path}\033\\Open File\033]8;;\033\\")
