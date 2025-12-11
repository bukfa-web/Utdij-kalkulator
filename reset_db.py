import sqlite3
import pandas as pd
import os

DB_FILE = "utdij_adatbazis.db"
CSV_2026 = "database.csv"
CSV_2025 = "database_2025.csv"

def tiszta_ujraepites():
    print("🧹 TAKARÍTÁS INDÍTÁSA...")
    
    # 1. Régi adatbázis törlése (Fizikai törlés)
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print(f"✅ Régi '{DB_FILE}' sikeresen törölve.")
        except PermissionError:
            print("❌ HIBA: Nem tudom törölni a fájlt! Zárd be a DB Browsert!")
            return
    else:
        print("ℹ️  Nem volt régi adatbázis.")

    # 2. Új adatbázis létrehozása
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE utszakaszok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ev INTEGER,
            ut_szam TEXT,
            azonosito TEXT,
            kezdo TEXT,
            veg TEXT,
            hossz_m INTEGER,
            tipus TEXT,
            szorzo REAL,
            UNIQUE(ev, azonosito)
        )
    ''')
    print("✅ Új, üres tábla létrehozva.")

    # 3. Adatok betöltése
    fajlok = [
        (2026, CSV_2026),
        (2025, CSV_2025)
    ]

    for ev, fajl in fajlok:
        if not os.path.exists(fajl):
            print(f"⚠️  HIÁNYZIK: {fajl} (Kihagyva)")
            continue

        print(f"🔄 {ev}-es adatok betöltése ({fajl})...")
        try:
            # Beolvasás
            try:
                df = pd.read_csv(fajl, sep=';', encoding='utf-8')
            except:
                df = pd.read_csv(fajl, sep=';', encoding='latin1')
            
            df.columns = df.columns.str.strip()

            count = 0
            for _, row in df.iterrows():
                try:
                    # Adatkonverzió
                    hossz = pd.to_numeric(str(row['Hossz']).replace(' ', '').replace(',', '.'), errors='coerce')
                    szorzo = pd.to_numeric(str(row['Szorzo']).replace(',', '.'), errors='coerce')
                    tipus = 'gyorsforgalmi' if 'gyors' in str(row['Tipus']).lower() else 'fout'
                    
                    # Beszúrás
                    cursor.execute('''
                        INSERT OR IGNORE INTO utszakaszok 
                        (ev, ut_szam, azonosito, kezdo, veg, hossz_m, tipus, szorzo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (ev, row['Ut'], row['Azonosito'], row['Kezdo'], row['Veg'], hossz, tipus, szorzo))
                    
                    if cursor.rowcount > 0:
                        count += 1
                except Exception as e:
                    pass # Egyedi hibás sorokat átugorjuk

            print(f"   ✅ {count} sor sikeresen betöltve.")

        except Exception as e:
            print(f"   ❌ Hiba a fájl feldolgozásakor: {e}")

    conn.commit()
    conn.close()
    print("\n🏁 KÉSZ! Ellenőrizd most a DB Browserben!")

if __name__ == "__main__":
    tiszta_ujraepites()