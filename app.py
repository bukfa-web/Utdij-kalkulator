from flask import Flask, render_template, request, jsonify
from main import UtdijKalkulator
import os

app = Flask(__name__)

# Adatbázis útvonal
DB_PATH = "utdij_adatbazis.db"

# Globális kalkulátor példány (indításkor egyszer létrejön)
kalkulator = UtdijKalkulator(DB_PATH)


@app.route('/', methods=['GET', 'POST'])
def index():
    # Főoldal – most már csak a településes/térképes felületet szolgálja ki
    return render_template('index.html')


# ------------------------------------------------------------------
# 1. Térképes kattintgatós számolás (több ponttal)
# ------------------------------------------------------------------
@app.route('/szamol_terkep', methods=['POST'])
def szamol_terkep():
    data = request.get_json()
    pontok = data.get('pontok', [])
    kategoria = data.get('kategoria', 'J5')
    ev = int(data.get('ev', 2026))

    if len(pontok) < 2:
        return jsonify({"hiba": "Legalább 2 pont szükséges!"})

    eredmeny = kalkulator.szamolas_terkep_pontokkal(pontok, kategoria=kategoria, ev=ev)
    return jsonify({"eredmeny": eredmeny})


# ------------------------------------------------------------------
# 2. Településes keresés (pl. Budapest → Szeged → Pécs)
#    → ugyanazt a számoló függvényt használja, mint a kattintgatós
# ------------------------------------------------------------------
@app.route('/szamol_telepulesekkel', methods=['POST'])
def szamol_telepulesekkel():
    data = request.get_json()
    pontok = data.get('pontok', [])
    ev = int(data.get('ev', 2026))
    kategoria = data.get('kategoria', 'J5')
    euro = data.get('euro', 'EURO6')
    netto_brutto = data.get('netto_brutto', 'netto')

    eredmeny = kalkulator.szamolas_terkep_pontokkal(pontok, ev, kategoria, euro, netto_brutto)
    return jsonify({"eredmeny": eredmeny})


# ------------------------------------------------------------------
# (Opcionális) Egy régi egyszerű route, ha valahol még használod
# ------------------------------------------------------------------
@app.route('/egyszeru', methods=['GET', 'POST'])
def egyszeru():
    # Ha később vissza akarod hozni a dropdown-os verziót
    return render_template('egyszeru.html')


if __name__ == '__main__':
    # Debug mód – fejlesztés közben nagyon hasznos
    app.run(debug=True)