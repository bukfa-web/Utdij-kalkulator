import sqlite3
import pandas as pd
import os

DB_FILE = "utdij_adatbazis.db"
CSV_2026 = "database_2026.csv" 
CSV_2025 = "database_2025.csv" 

# Az elvárt oszlopnevek a CSV-ben (a kódolás miatti Sorszám is számít)
CLEAN_HEADERS = ['Sorszám', 'Ut', 'Azonosito', 'Kezdo', 'Veg', 'Hossz', 'Tipus', 'Szorzo']

def adatbazis_frissites():
    # Először töröljük a régi, hibás adatbázist
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print("🗑️ Régi adatbázis törölve.")
        except PermissionError:
            print("❌ HIBA: Kérlek, zárd be a DB Browser for SQLite programot!")
            return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Adatbázis szerkezet létrehozása (Duplikáció védelemmel: UNIQUE(ev, azonosito))
    cursor.execute('''
        CREATE TABLE utszakaszok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ev INTEGER,
            ut_szam TEXT,
            azonosito TEXT,
            kezdo TEXT,
            veg TEXT,
            hossz_m REAL,
            tipus TEXT,
            szorzo REAL,
            UNIQUE(ev, azonosito)
        )
    ''')
    print("✅ Adatbázis szerkezet készen.")

    # ----------------------------------------------------
    # Fájlok betöltése (2026 és 2025)
    # ----------------------------------------------------
    
    # Feltételezzük: pontosvessző (;) elválasztó
    for ev, csv_nev in [(2026, CSV_2026), (2025, CSV_2025)]:
        if not os.path.exists(csv_nev):
            print(f"\n❌ HIÁNYZIK: A {csv_nev} fájl nem található.")
            continue

        print(f"\n🔄 {ev}-es adatok betöltése ({csv_nev})...")
        
        try:
            # Fejléc olvasás: 0. sor fejléc, Skiprows=1, hogy átugorjuk az üres, technikai sort
            df = pd.read_csv(csv_nev, sep=';', encoding='latin1', header=0, skiprows=1) 
            df.columns = df.columns.str.strip()
            
            # Ellenőrzés: Az Ut oszlopot keresi, de a beolvasásnál az első oszlop az Ut. 
            # A skiprows=1 miatt az oszlopok eggyel elcsúsznak.
            
            # Kézzel beállítjuk az oszlopokat, hogy a kód ne keressen, hanem tudja a helyét.
            df = df.iloc[:, :len(CLEAN_HEADERS)].copy()
            df.columns = CLEAN_HEADERS
            
            # Tisztítás és Konverzió
            df = df[df['Ut'].notna()]
            df['Ut_szam'] = df['Ut'].astype(str).str.strip()
            df['Tipus'] = df['Tipus'].astype(str).apply(lambda x: 'gyorsforgalmi' if 'gyors' in x.lower() else 'fout')
            
            # Robusztus Vessző -> Pont konverzió (visszatartja a null értékeket is)
            df['Hossz_m'] = pd.to_numeric(df['Hossz'].astype(str).str.replace(' ', '').str.replace(',', '.', regex=False), errors='coerce').fillna(0)
            df['Szorzo'] = pd.to_numeric(df['Szorzo'].astype(str).str.replace(' ', '').str.replace(',', '.', regex=False), errors='coerce').fillna(0)
            
            # Beszúrás az adatbázisba
            count = 0
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO utszakaszok 
                        (ev, ut_szam, azonosito, kezdo, veg, hossz_m, tipus, szorzo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (ev, row['Ut_szam'], row['Azonosito'], row['Kezdo'], row['Veg'], row['Hossz_m'], row['Tipus'], row['Szorzo']))
                    if cursor.rowcount > 0: count += 1
                except Exception:
                    pass
            
            osszes_sor = len(df)
            duplikatumok = osszes_sor - count
            
            print(f"   --> Összes sor a CSV-ből: {osszes_sor}")
            print(f"   ✅ Új szakaszok rögzítve: {count} db")
            print(f"   ⚠️ Kihagyott duplikátumok/hiba: {duplikatumok} db")
        
        except Exception as e:
            print(f"   ❌ Súlyos hiba a fájl feldolgozásakor: {e}")
            print("   (Valószínűleg a fejlécek elcsúszása miatt. Ellenőrizd a CSV oszlopokat!)")

    conn.commit()
    conn.close()
    print("\n🏁 Folyamat befejezve. Futtasd a python app.py-t az eredményekért!")

if __name__ == "__main__":
    adatbazis_frissites()