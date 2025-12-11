import sqlite3
import os
import math
import requests  # OSRM routinghoz
from haversine import haversine  # Távolság fallback
from geopy.geocoders import Nominatim  # Település geokódolás
from geopy.exc import GeocoderTimedOut

AFA = 1.27  # Bruttó / AFA = nettó

class UtdijKalkulator:
    def __init__(self, db_path="utdij_adatbazis.db"):
        self.db_path = db_path
        self.geolocator = Nominatim(user_agent="utdij_kalkulator", timeout=10)  # Geopy timeout 10s
        # Fallback koordináták benchmarkhoz
        self.fallback_coords = {
            "Szekszárd": (46.35, 18.70),
            "Cece": (46.71, 18.21),
            "Nemesszalók": (46.62, 18.39)
        }

    def get_tariffs(self, kategoria, ev, euro):
        """Díjak lekérdezése tariffs táblából"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT infra_gyors, infra_fo, kulso_lezajo, co2 FROM tariffs 
            WHERE kategoria = ? AND ev = ? AND euro = ?
            """
            result = conn.execute(query, (kategoria, ev, euro)).fetchone()
            conn.close()
            if result:
                return result  # (infra_gyors, infra_fo, kulso_lezajo, co2) bruttó Ft/km
        except Exception as e:
            print(f"DB hiba tariffs-nél: {e}")
        # Fallback ha DB üres (manuális J5 EURO6)
        fallback = {
            2025: (163.89, 101.78, 16.78, 39.48),
            2026: (170.94, 157.05, 16.78, 39.48)
        }
        return fallback.get(ev, (0, 0, 0, 0))

    def get_sections(self, ev):
        """Minden szakasz lekérdezése évre"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT ut_szam, azonosito, kezdo, veg, hossz_m, tipus, szorzo
        FROM utszakaszok WHERE ev = ? ORDER BY ut_szam
        """
        result = conn.execute(query, (ev,)).fetchall()
        conn.close()
        return result

    def geocode_telepules(self, nev):
        """Településnév → koordináta (geopy, fallback manual)"""
        try:
            location = self.geolocator.geocode(nev + ", Magyarország")
            if location:
                return {"lat": location.latitude, "lon": location.longitude}
        except GeocoderTimedOut:
            print(f"Geokódolás timeout: {nev}")
        # Fallback manual koordináták
        if nev in self.fallback_coords:
            lat, lon = self.fallback_coords[nev]
            return {"lat": lat, "lon": lon}
        return None

    def get_real_km(self, pontok):
        """Valódi útvonal kumulatív km (OSRM vagy haversine)"""
        if len(pontok) < 2:
            return [0.0]
        coords = ";".join(f"{p['lon']},{p['lat']}" for p in pontok)
        url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=false&alternatives=false"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if "routes" in data and data["routes"]:
                    route = data["routes"][0]
                    kumulativ = [0.0]
                    for leg in route["legs"]:
                        kumulativ.append(kumulativ[-1] + leg["distance"] / 1000.0)
                    return kumulativ
        except Exception as e:
            print(f"OSRM hiba: {e}")
        # Fallback haversine
        kumulativ = [0.0]
        for i in range(1, len(pontok)):
            p1 = pontok[i-1]
            p2 = pontok[i]
            d = haversine((p1['lat'], p1['lon']), (p2['lat'], p2['lon']))
            kumulativ.append(kumulativ[-1] + d)
        return kumulativ

    def szelveny_num(self, s):
        """Szelvény konverter km-re"""
        if not isinstance(s, str) or '+' not in s:
            return 0.0
        s = s.replace(' ', '')
        s = s.replace('+', '.')
        try:
            return float(s)
        except ValueError:
            return 0.0

    def szamolas_terkep_pontokkal(self, pontok_input, ev=2025, kategoria="J5", euro="EURO6", netto_brutto="netto"):
        """Fő számítás: pontokból útvonal, arányos díj (fixelt scale nélkül)"""
        if isinstance(pontok_input, str):  # Település string
            telepulesek = pontok_input.split(" → ")
            pontok = []
            for nev in telepulesek:
                coord = self.geocode_telepules(nev.strip())
                if coord:
                    pontok.append(coord)
                else:
                    return f"<span style='color:red'>Geokódolás hiba: {nev}</span>"
            if len(pontok) < 2:
                return "<span style='color:red'>Legalább 2 település szükséges!</span>"
        else:
            pontok = pontok_input

        # 1. Útvonal kumulatív km
        kumulativ = self.get_real_km(pontok)
        osszes_tav = kumulativ[-1]
        if osszes_tav == 0:
            return "<span style='color:red'>Hiba a távolság számításban!</span>"

        # 2. Szakaszok lekérdezés
        szakaszok = self.get_sections(ev)
        if not szakaszok:
            return f"<span style='color:red'>Nincs szakasz adat {ev}-re!</span>"

        # 3. Díjak lekérdezés
        infra_gyors, infra_fo, kulso_lezajo, co2 = self.get_tariffs(kategoria, ev, euro)
        netto_factor = 1 / AFA if netto_brutto == "netto" else 1.0

        # 4. Arányos atfedes (route_km / db_total * hossz_km)
        db_total_hossz_km = sum(s[4] for s in szakaszok) / 1000.0
        osszdij = 0.0
        kimutatas = f"<h3>{ev} - {kategoria} - {euro} - Teljes: {osszes_tav:.1f} km</h3><ol>"

        for i in range(len(pontok) - 1):
            k = kumulativ[i]
            v = kumulativ[i + 1]
            resz_tav = v - k
            resz_dij = 0.0
            kimutatas += f"<li>Szakasz {i+1} ({resz_tav:.1f} km):<br>"

            for ut, azono, kezdo, veg, hossz, tipus, szorzo in szakaszok:
                hossz_km = hossz / 1000.0
                atfedes = resz_tav * (hossz_km / db_total_hossz_km)  # Arányos
                if atfedes > 0:
                    infra = infra_gyors if "gyorsforgalmi" in tipus else infra_fo
                    rate_brutto = infra + (kulso_lezajo * szorzo) + co2
                    dij_resz = atfedes * rate_brutto * netto_factor
                    resz_dij += dij_resz
                    kimutatas += f"  • {ut} {azono}: {atfedes:.2f} km × {rate_brutto:.1f} Ft/km × {szorzo:.3f} = {dij_resz:,.0f} Ft<br>"

            osszdij += resz_dij
            kimutatas += f"  <b>Rész: {resz_dij:,.0f} Ft</b></li>"

        kimutatas += "</ol>"
        kimutatas += f"<h2 style='color:green'>Összesen: <b>{osszdij:,.0f} Ft ({netto_brutto.upper()})</b></h2>"
        kimutatas += f"<small>Átlag: {osszdij / osszes_tav:.2f} Ft/km</small>"

        return kimutatas

# Teszt
if __name__ == "__main__":
    kalk = UtdijKalkulator()
    eredmeny = kalk.szamolas_terkep_pontokkal("Szekszárd → Cece → Nemesszalók", ev=2025, kategoria="J5", euro="EURO6", netto_brutto="netto")
    print(eredmeny[:500] + "...")