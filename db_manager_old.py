# db_manager.py – VÉGLEGES: Díjtábla teljes rögzítése (minden kategória, minden EURO osztály)
import sqlite3
import pandas as pd
import os

DB_FILE = "utdij_adatbazis.db"
EXCEL_DIJ = "Adatok/dijtabla_2025_2026.xlsx"  # Pontos fájlnév!
AFA = 1.27

def adatbazis_dijtabla_frissites():
    if not os.path.exists(EXCEL_DIJ):
        print(f"⚠️ FIGYELEM: Díjtábla Excel hiányzik: {EXCEL_DIJ}")
        print("   A díjak nem lesznek rögzítve – a program fallback díjakkal fog futni.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Díjtábla létrehozása (ha még nincs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tariffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategoria TEXT,
            ev INTEGER,
            euro_osztaly TEXT,
            infra_gyors_brutto REAL,
            infra_gyors_netto REAL,
            infra_fo_brutto REAL,
            infra_fo_netto REAL,
            kulso_kulvaros_brutto REAL,
            kulso_kulvaros_netto REAL,
            kulso_telep_brutto REAL,
            kulso_telep_netto REAL,
            co2_brutto REAL,
            co2_netto REAL,
            UNIQUE(kategoria, ev, euro_osztaly)
        )
    ''')
    print("✅ Díjtábla struktúra kész vagy ellenőrizve.")

    xl = pd.ExcelFile(EXCEL_DIJ)
    count = 0
    for ev_str in ["2025", "2026"]:
        if f"{ev_str} díjszámítás" not in xl.sheet_names:
            print(f"⚠️ Lap hiányzik: {ev_str} díjszámítás")
            continue

        df = xl.parse(f"{ev_str} díjszámítás", header=None)
        ev = int(ev_str)

        # Minden sorban keresünk kategóriát (J3, J4, J5 stb.)
        for _, row in df.iterrows():
            kategoria_cell = str(row[0])
            if not any(k in kategoria_cell for k in ["J3", "J4", "J5", "J2"]):
                continue  # Nem díjsoros

            # EURO osztály keresése a sorban (általában oszlop 12 vagy közel)
            euro_osztaly = "Ismeretlen"
            for cell in row:
                cell_str = str(cell)
                if "EURO" in cell_str or "alacsony" in cell_str.lower() or "kibocsátásmentes" in cell_str.lower():
                    euro_osztaly = cell_str.strip()
                    break

            # Díjak (oszlopok a hivatalos tábla szerint)
            infra_gyors_brutto = pd.to_numeric(row[1], errors='coerce') or 0
            infra_fo_brutto = pd.to_numeric(row[4], errors='coerce') or 0
            kulso_kulvaros_brutto = pd.to_numeric(row[7], errors='coerce') or 0
            kulso_telep_brutto = pd.to_numeric(row[9], errors='coerce') or 0
            co2_brutto = pd.to_numeric(row[11], errors='coerce') or 0

            # Nettó kiszámolása
            infra_gyors_netto = round(infra_gyors_brutto / AFA, 2)
            infra_fo_netto = round(infra_fo_brutto / AFA, 2)
            kulso_kulvaros_netto = round(kulso_kulvaros_brutto / AFA, 2)
            kulso_telep_netto = round(kulso_telep_brutto / AFA, 2)
            co2_netto = round(co2_brutto / AFA, 2)

            # Kategória kinyerése (pl. "J5")
            kategoria = next((k for k in ["J3", "J4", "J5", "J2"] if k in kategoria_cell), "Ismeretlen")

            # Beszúrás vagy frissítés
            cursor.execute('''
                INSERT OR REPLACE INTO tariffs
                (kategoria, ev, euro_osztaly,
                 infra_gyors_brutto, infra_gyors_netto,
                 infra_fo_brutto, infra_fo_netto,
                 kulso_kulvaros_brutto, kulso_kulvaros_netto,
                 kulso_telep_brutto, kulso_telep_netto,
                 co2_brutto, co2_netto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (kategoria, ev, euro_osztaly,
                  infra_gyors_brutto, infra_gyors_netto,
                  infra_fo_brutto, infra_fo_netto,
                  kulso_kulvaros_brutto, kulso_kulvaros_netto,
                  kulso_telep_brutto, kulso_telep_netto,
                  co2_brutto, co2_netto))

            count += 1

    conn.commit()
    conn.close()
    print(f"✅ Díjtábla rögzítve: {count} sor (minden kategória és EURO osztály).")
    print("   Most már a program csak az adatbázist használja – soha többé nem kell Excel!")

if __name__ == "__main__":
    adatbazis_dijtabla_frissites()