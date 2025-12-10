import pandas as pd
import os

class UtdijKalkulator:
    def __init__(self, csv_utvonal):
        # 1. INFRASTRUKTÚRADÍJ (BRUTTÓ Ft/km) - 2026. jan. 1-től
        # Forrás: 375/2025. Korm. rendelet
        self.infra_dijak_brutto = {
            "J2": {"gyorsforgalmi": 65.89, "fout": 53.30},
            "J3": {"gyorsforgalmi": 105.32, "fout": 88.15},
            "J4": {"gyorsforgalmi": 163.26, "fout": 150.97},
            "J5": {"gyorsforgalmi": 170.94, "fout": 157.05}
        }

        # 2. KÜLSŐKÖLTSÉGDÍJ (NETTÓ Ft/km) - Becsült átlag (Euro VI)
        # Forrás: NFM rendelet struktúrája (Nettó -> Bruttósítani kell)
        self.kulsokoltseg_netto = {
            "J2": {"gyorsforgalmi": 12.50, "fout": 5.50},
            "J3": {"gyorsforgalmi": 18.20, "fout": 8.10},
            "J4": {"gyorsforgalmi": 25.40, "fout": 12.30},
            "J5": {"gyorsforgalmi": 30.10, "fout": 15.20}
        }

        # 3. ÚTHÁLÓZAT BETÖLTÉSE
        try:
            # Pontosvesszővel elválasztott CSV kezelése
            self.uthalozat = pd.read_csv(csv_utvonal, sep=';', encoding='utf-8')
            
            # Oszlopnevek tisztítása
            self.uthalozat.columns = self.uthalozat.columns.str.strip()
            
            # Tipus normalizálása (hogy a kód értse: 'gyorsforgalmi' vagy 'fout')
            # Feltételezzük, hogy a CSV-ben az oszlop neve 'Infrastruktúradíj-szint'
            # Ha nem találja, megpróbáljuk a 'Tipus' oszlopot
            col_tipus = 'Infrastruktúradíj-szint' if 'Infrastruktúradíj-szint' in self.uthalozat.columns else 'Tipus'
            
            self.uthalozat['Tipus_Kod'] = self.uthalozat[col_tipus].apply(
                lambda x: 'gyorsforgalmi' if 'gyors' in str(x).lower() else 'fout'
            )
            print(f"✅ Adatbázis betöltve: {len(self.uthalozat)} útszakasz.")
            
        except Exception as e:
            print(f"❌ HIBA: Nem sikerült betölteni a {csv_utvonal} fájlt.")
            print(f"Részletek: {e}")
            self.uthalozat = None

    def szamolas(self, jarmu_kat, ut_nev):
        if self.uthalozat is None: return "Hiba: Nincs adatbázis."
        if jarmu_kat not in self.infra_dijak_brutto: return "Hiba: Ismeretlen kategória (pl. J2, J5)."

        # Szűrés az útra (pl. "M1")
        # Feltételezzük, hogy az út neve az 'Útdíjfizetési kötelezettséggel érintett út száma' oszlopban van
        # Vagy egyszerűen 'Ut' oszlopban
        col_ut = 'Útdíjfizetési kötelezettséggel érintett út száma' if 'Útdíjfizetési kötelezettséggel érintett út száma' in self.uthalozat.columns else 'Ut'
        
        szurt = self.uthalozat[self.uthalozat[col_ut].astype(str) == str(ut_nev)]

        if szurt.empty:
            return f"Nincs adat a(z) {ut_nev} útról."

        osszesen = {"km": 0, "infra_brutto": 0, "kulso_netto": 0, "kulso_brutto": 0}

        for _, sor in szurt.iterrows():
            # Hossz kezelése (méterben van, átváltjuk km-re)
            # Kezeljük a tizedesvesszőt (pl. "1,5" -> 1.5)
            raw_hossz = str(sor.get('ED szakasz hossz (m)', sor.get('Hossz_m', 0)))
            hossz_m = float(raw_hossz.replace(',', '.'))
            hossz_km = hossz_m / 1000.0
            
            tipus = sor['Tipus_Kod']
            
            # Számítás
            infra = hossz_km * self.infra_dijak_brutto[jarmu_kat][tipus]
            kulso_n = hossz_km * self.kulsokoltseg_netto[jarmu_kat][tipus]
            kulso_b = kulso_n * 1.27 # ÁFA

            osszesen["km"] += hossz_km
            osszesen["infra_brutto"] += infra
            osszesen["kulso_netto"] += kulso_n
            osszesen["kulso_brutto"] += kulso_b

        total = osszesen["infra_brutto"] + osszesen["kulso_brutto"]
        
        return (
            f"\n=== KALKULÁCIÓ: {ut_nev} ({jarmu_kat}) ===\n"
            f"Távolság:           {osszesen['km']:.2f} km\n"
            f"----------------------------------------\n"
            f"Infrastruktúradíj:  {osszesen['infra_brutto']:.0f} Ft (Bruttó)\n"
            f"Külsőköltségdíj:    {osszesen['kulso_brutto']:.0f} Ft (Bruttó)\n"
            f"----------------------------------------\n"
            f"VÉGÖSSZEG:          {total:.0f} Ft"
        )

# --- Futtatás ---
if __name__ == "__main__":
    # Itt add meg a CSV fájl pontos nevét!
    db_file = "database.csv"
    
    if os.path.exists(db_file):
        app = UtdijKalkulator(db_file)
        
        # Példa futtatás
        print(app.szamolas("J5", "M1"))
        print(app.szamolas("J4", "86"))
    else:
        print(f"Kérlek, nevezd át a letöltött CSV fájlt erre: {db_file}")