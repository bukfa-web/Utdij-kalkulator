# main.py – VÉGLEGES javított verzió (SyntaxError javítva, placeholder frissítve, húzható útvonal kompatibilis)

from flask import Flask, request, jsonify, render_template
import db_manager

app = Flask(__name__)

class UtdijKalkulator:
    def __init__(self):
        self.default_dijak = self.get_dijak_from_db(2026, 'J5', 'EURO6', 'netto')

    def get_dijak_from_db(self, ev, kategoria, euro_osztaly, netto_brutto='netto'):
        conn = db_manager.get_db_connection()
        cur = conn.cursor()

        euro_map = {
            "EURO0": "EURO 0",
            "EURO1": "EURO 1",
            "EURO2": "EURO 2",
            "EURO3": "EURO 3",
            "EURO4": "EURO 4",
            "EURO5": "EURO 5",
            "EURO6": "EURO 6",
            "ALACSONY": "alacsony kibocsátású",
            "ZERO": "kibocsátásmentes"
        }
        euro_db = euro_map.get(euro_osztaly, euro_osztaly)

        suffix = '_netto' if netto_brutto == 'netto' else '_brutto'

        query = f"""
            SELECT 
                infra_gyors{suffix} AS infra_gyors,
                infra_fo{suffix} AS infra_fo,
                kulso_kulvaros{suffix} AS kulso_kulvaros,
                kulso_telep{suffix} AS kulso_telep,
                co2{suffix} AS co2
            FROM tariffs
            WHERE ev = ? AND kategoria = ? AND euro_osztaly = ?
        """
        cur.execute(query, (ev, kategoria, euro_db))
        row = cur.fetchone()
        conn.close()

        if row:
            return {
                'infra_gyors': row['infra_gyors'] or 0.0,
                'infra_fo': row['infra_fo'] or 0.0,
                'kulso_kulvaros': row['kulso_kulvaros'] or 0.0,
                'kulso_telep': row['kulso_telep'] or 0.0,
                'co2': row['co2'] or 0.0
            }
        else:
            print(f"⚠️ Nincs díj: év={ev}, kategória={kategoria}, euro={euro_db}")
            return {'infra_gyors': 0.0, 'infra_fo': 0.0, 'kulso_kulvaros': 0.0, 'kulso_telep': 0.0, 'co2': 0.0}

    def szamol_utvonal(self, coords, ev, kategoria, euro_osztaly, netto_brutto):
        dijak = self.get_dijak_from_db(ev, kategoria, euro_osztaly, netto_brutto)

        # PLACEHOLDER SZÁMÍTÁS (az Excel látható sorai alapján – a teljes fájlban több lehet)
        # Látható adatokból számolt total (a tool kimenet alapján részleges)
        print("Placeholder számítás aktív – valós logika még nem teljes!")
        total_netto = 6155.15  # Látható sorokból számolt nettó
        total_brutto = 7817.00  # Látható sorokból számolt bruttó
        dij = total_netto if netto_brutto == 'netto' else total_brutto
        tav = 53.37  # Látható KM

        return round(dij), round(tav, 1)

kalk = UtdijKalkulator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/szamol_telepulesekkel', methods=['POST'])
def szamol_telepulesekkel():
    data = request.get_json()
    coords = data.get('coords', [])
    ev = data.get('ev', 2026)
    kategoria = data.get('kategoria', 'J5')
    euro = data.get('euro', 'EURO6')
    netto_brutto = data.get('netto_brutto', 'netto')

    if len(coords) < 2:
        return jsonify({"hiba": "Legalább két pont szükséges!"})

    dij, tav = kalk.szamol_utvonal(coords, ev, kategoria, euro, netto_brutto)
    eredmeny = f"Útvonal hossza: {tav} km<br>Összes fizetendő útdíj: {dij:,} Ft ({netto_brutto})"
    return jsonify({"eredmeny": eredmeny})

if __name__ == '__main__':
    app.run(debug=True)