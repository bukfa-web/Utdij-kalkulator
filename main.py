import sqlite3
import os
import math

AFA = 1.27

class UtdijKalkulator:
    def __init__(self, db_path="utdij_adatbazis.db"):
        self.db_path = db_path

        # 2025 és 2026 díjak – hivatalos NÚSZ táblázatból (bruttó Ft/km)
        self.dijak_brutto = {
            2025: {
                "J2": {"infra_gy": 63.17, "infra_f": 34.54, "kulso": {"EURO6": 11.35, "ALACSONY": 9.87, "ZERO": 0.0}},
                "J3": {"infra_gy": 100.98, "infra_f": 57.13, "kulso": {"EURO6": 13.82, "ALACSONY": 11.35, "ZERO": 0.0}},
                "J4": {"infra_gy": 156.53, "infra_f": 97.84, "kulso": {"EURO6": 15.30, "ALACSONY": 12.34, "ZERO": 0.0}},
                "J5": {"infra_gy": 163.89, "infra_f": 101.78, "kulso": {"EURO6": 16.78, "ALACSONY": 13.82, "ZERO": 0.0}}
            },
            2026: {
                "J2": {"infra_gy": 65.89, "infra_f": 53.30, "kulso": {"EURO6": 11.35, "ALACSONY": 9.87, "ZERO": 0.0}},
                "J3": {"infra_gy": 105.32, "infra_f": 88.15, "kulso": {"EURO6": 13.82, "ALACSONY": 11.35, "ZERO": 0.0}},
                "J4": {"infra_gy": 163.26, "infra_f": 150.97, "kulso": {"EURO6": 15.30, "ALACSONY": 12.34, "ZERO": 0.0}},
                "J5": {"infra_gy": 170.94, "infra_f": 157.05, "kulso": {"EURO6": 16.78, "ALACSONY": 13.82, "ZERO": 0.0}}
            }
        }

    def szamolas_terkep_pontokkal(self, pontok_list, ev=2026, kategoria="J5", euro="EURO6", netto_brutto="netto"):
        if len(pontok_list) < 2:
            return "<span style='color:red'>Legalább 2 pont szükséges!</span>"

        if ev not in self.dijak_brutto:
            return "<span style='color:red'>Év nem támogatott!</span>"

        dij = self.dijak_brutto[ev][kategoria]

        # Kumulativ távolság
        kumulativ = [0.0]
        for i in range(1, len(pontok_list)):
            p1, p2 = pontok_list[i-1], pontok_list[i]
            tav = math.dist((p1['lat'], p1['lon']), (p2['lat'], p2['lon'])) * 111.32  # kb. km
            kumulativ.append(kumulativ[-1] + tav)

        # DB szakaszok (61-es teszt útra)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT kezdo, veg, hossz_m, tipus, szorzo FROM utszakaszok WHERE ev=? AND ut_szam='61' ORDER BY CAST(REPLACE(kezdo,' + ','.') AS REAL)", (ev,))
        szakaszok = cur.fetchall()
        conn.close()

        def szelveny_num(s): return float(s.replace(" + ", ".").replace(" ", ""))

        osszdij = 0.0
        kimutatas = f"<h3>Útvonal számítás – {ev}, {kategoria}, {euro}</h3><ol>"

        for i in range(len(pontok_list)-1):
            k = kumulativ[i]
            v = kumulativ[i+1]
            resz_dij = 0.0
            kimutatas += f"<li>Szakasz {i+1} ({v-k:.1f} km):<br>"

            for kezdo_str, veg_str, hossz_m, tipus, szorzo in szakaszok:
                k_db = szelveny_num(kezdo_str)
                v_db = szelveny_num(veg_str)
                atfedes = max(0, min(v, v_db) - max(k, k_db))
                if atfedes > 0:
                    infra = dij["infra_gy"] if "gyors" in tipus else dij["infra_f"]
                    kulso = dij["kulso"].get(euro, 0.0)
                    rate = infra + kulso
                    dij_resz = atfedes * rate * szorzo
                    if netto_brutto == "netto":
                        dij_resz /= AFA
                    resz_dij += dij_resz
                    kimutatas += f"  • {atfedes:.2f} km × {rate:.1f} Ft/km × {szorzo:.3f} = {dij_resz:,.0f} Ft<br>"
            osszdij += resz_dij
            kimutatas += f"  <b>Részösszeg: {resz_dij:,.0f} Ft</b></li>"

        kimutatas += "</ol>"
        if netto_brutto == "netto":
            osszdij /= AFA
        kimutatas += f"<h2 style='color:green'>Összesen: <b>{osszdij:,.0f} Ft ({netto_brutto.upper()})</b></h2>"
        return kimutatas