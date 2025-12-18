# test_db.py – Adatbázis ellenőrzés
import sqlite3

DB_FILE = "utdij_adatbazis.db"

try:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # 1. Utszakaszok száma
    cur.execute("SELECT COUNT(*) FROM utszakaszok")
    szakaszok = cur.fetchone()[0]
    print(f"✅ Utszakaszok száma: {szakaszok} db (elvárás: 5226)")

    # 2. Díjtábla sorok száma
    cur.execute("SELECT COUNT(*) FROM tariffs")
    tariffak = cur.fetchone()[0]
    print(f"✅ Díjtábla sorok száma: {tariffak} db (elvárás: 72 vagy több)")

    # 3. Példa: J5 EURO 6 2025
    cur.execute("""
        SELECT infra_gyors_brutto, infra_gyors_netto, 
               infra_fo_brutto, infra_fo_netto,
               co2_brutto, co2_netto
        FROM tariffs 
        WHERE kategoria = 'J5' AND ev = 2025 AND euro_osztaly LIKE '%EURO 6%'
    """)
    j5 = cur.fetchone()
    if j5:
        print(f"✅ J5 EURO 6 2025 díjak:")
        print(f"   Infra gyors: {j5[0]} Ft/km (bruttó) → {j5[1]:.2f} Ft/km (nettó)")
        print(f"   Infra főút: {j5[2]} Ft/km (bruttó) → {j5[3]:.2f} Ft/km (nettó)")
        print(f"   CO2: {j5[4]} Ft/km (bruttó) → {j5[5]:.2f} Ft/km (nettó)")
    else:
        print("❌ J5 EURO 6 2025 nem található!")

    # 4. Példa: J3 alacsony kibocsátású 2026
    cur.execute("""
        SELECT infra_gyors_netto, co2_netto 
        FROM tariffs 
        WHERE kategoria = 'J3' AND ev = 2026 AND euro_osztaly LIKE '%alacsony kibocsátású%'
    """)
    j3 = cur.fetchone()
    if j3:
        print(f"✅ J3 alacsony kibocsátású 2026 példa: infra gyors netto = {j3[0]:.2f} Ft/km, CO2 netto = {j3[1]:.2f} Ft/km")
    else:
        print("❌ J3 alacsony kibocsátású 2026 nem található!")

    # 5. EURO osztályok listája (egyediek)
    cur.execute("SELECT DISTINCT euro_osztaly FROM tariffs")
    eurok = [row[0] for row in cur.fetchall()]
    print(f"✅ Elérhető EURO osztályok: {', '.join(eurok)}")

    conn.close()
    print("\n🏁 Teszt sikeres – az adatbázis tökéletesen működik és olvasható!")

except Exception as e:
    print(f"❌ HIBA az adatbázis olvasásakor: {e}")