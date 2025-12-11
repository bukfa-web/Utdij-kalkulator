import sqlite3
import pandas as pd
import os

DB_FILE = "utdij_adatbazis.db"
CSV_2026 = r"C:\Utdij kalkulator\Adatok\database_2026.csv" 
CSV_2025 = r"C:\Utdij kalkulator\Adatok\database_2025.csv" 

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
            # Fejléc olvasás: 0. sor fejléc, NINCS skiprows, mert a BOM után a header jó
            df = pd.read_csv(csv_nev, sep=';', encoding='latin1', header=0) 
            df.columns = df.columns.str.strip()
            
            # Kézzel beállítjuk az oszlopokat, ha szükséges (de a header jó, szóval csak tisztítunk)
            if len(df.columns) < len(CLEAN_HEADERS):
                print(f"⚠️ Oszlopok száma nem egyezik: {len(df.columns)} vs. {len(CLEAN_HEADERS)} – ellenőrizd!")
            df = df.iloc[:, :len(CLEAN_HEADERS)].copy()
            df.columns = CLEAN_HEADERS
            
            # Tisztítás és Konverzió
            df = df[df['Ut'].notna()]
            df['Ut_szam'] = df['Ut'].astype(str).str.strip()
            df['Tipus'] = df['Tipus'].astype(str).apply(lambda x: 'gyorsforgalmi' if 'gyors' in x.lower() else 'főúti')
            
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

    # ÚJ RÉSZ: Tariffs tábla hozzáadása (Excel parse, fixelt row indexekkel)
    excel_file = r"C:\Utdij kalkulator\Adatok\Öszesített díj tábla 2025-2026 .xlsx"
    if os.path.exists(excel_file):
        print("\n🔄 Díjak feltöltése az Excel-ből...")
        try:
            # Tábla létrehozása
            cursor.execute('''
                CREATE TABLE tariffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kategoria TEXT,
                    ev INTEGER,
                    euro TEXT,
                    infra_gyors REAL,
                    infra_fo REAL,
                    kulso_lezajo REAL,
                    co2 REAL,
                    UNIQUE(kategoria, ev, euro)
                )
            ''')
            sheet_2025 = pd.read_excel(excel_file, sheet_name='2025 díjszámítás', header=None)
            sheet_2026 = pd.read_excel(excel_file, sheet_name='2026 díjszámítás', header=None)

            def parse_sheet(sheet, ev):
                data = []
                euros = ['EURO0', 'EURO1', 'EURO2', 'EURO3', 'EURO4', 'EURO5', 'EURO6', 'alacsony', 'kibocsat']
                # Fixelt row indexek: iloc[4]=row5=J2, iloc[13]=row14=J3, stb. (0-indexelt)
                for kat, start_row in [('J2', 4), ('J3', 13), ('J4', 22), ('J5', 31)]:
                    end_row = min(start_row + 9, len(sheet))  # Bounds check
                    if end_row <= start_row:
                        print(f"   ⚠️ Rövid sheet {kat}-ra: {start_row} - {end_row}")
                        continue
                    # Oszlopok: B=1 (gyors), F=5 (fo), I=8 (kulso), L=11 (co2)
                    gyors = pd.to_numeric(sheet.iloc[start_row:end_row, 1], errors='coerce').fillna(0).tolist()
                    fo = pd.to_numeric(sheet.iloc[start_row:end_row, 5], errors='coerce').fillna(0).tolist()
                    lezajo = pd.to_numeric(sheet.iloc[start_row:end_row, 8], errors='coerce').fillna(0).tolist()
                    co2_list = pd.to_numeric(sheet.iloc[start_row:end_row, 11], errors='coerce').fillna(0).tolist()
                    for i, euro in enumerate(euros):
                        if i < len(gyors):
                            data.append((kat, ev, euro, gyors[i], fo[i], lezajo[i], co2_list[i]))
                return data

            tariffs_list = parse_sheet(sheet_2025, 2025) + parse_sheet(sheet_2026, 2026)
            count_tariff = 0
            for row in tariffs_list:
                cursor.execute('''
                    INSERT OR IGNORE INTO tariffs (kategoria, ev, euro, infra_gyors, infra_fo, kulso_lezajo, co2)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', row)
                count_tariff += cursor.rowcount
            print(f"   ✅ Díjak feltöltve: {count_tariff} sor")
        except Exception as e:
            print(f"   ❌ Excel hiba: {e}")
            # Debug print: sheet info
            try:
                sheet_test = pd.read_excel(excel_file, sheet_name='2025 díjszámítás', header=None)
                print(f"   Debug: Sheet shape: {sheet_test.shape}, first 5 rows (columns 0-12):")
                print(sheet_test.iloc[0:5, 0:12].to_string())
            except:
                pass
    else:
        print(f"\n⚠️ Excel hiányzik: {excel_file} – ellenőrizd a nevet a mappában (`dir Adatok`).")

    conn.commit()
    conn.close()
    print("\n🏁 Folyamat befejezve. Futtasd a python app.py-t az eredményekért!")

if __name__ == "__main__":
    adatbazis_frissites()