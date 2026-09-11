'''
1. IMPORT: Importiere die Funktion 'search_lightcurve' aus dem Modul 'lightkurve'
2. TARGET: Estelle eine Variable fuer das Ziel-Objekt (Stern: "Kepler-10")
3. SUCHE: Verfasse eine Abfrage mit 'search_lightcurve':
    - Uebergib den Zielnamen.
    - Setze das Argument mission="Kepler", um gezielt im Kepler-Archiv zu suchen.
4. AUSGABE: Gib das Suchergebnis mit print() in der Konsole aus, um die verfuegbaren Beobachtungs-Quartale zu sehen.
5. DOWNLOAD: Waehle den ersten Eintrag der Suchergebnisse aus (Index[0]) und wende darauf die Methode .download() an.
6. VERIFIKATION: Gib das heruntergeladene Objekt per print() aus.
'''
from lightkurve import search_lightcurve
target_object = "Kepler-10"

result = search_lightcurve(target_object, mission="Kepler")
print(result)

print("\n"+25*'='+"\n")

downloaded = result[0].download()
print(downloaded)