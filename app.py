from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from db_manager import get_db_connection
from kalkulator import szamol_dij

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'  # Termelésben cseréld erősebbre
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/', methods=['GET', 'POST'])
def params():
    if request.method == 'POST':
        session['ev'] = request.form['ev']
        session['kategoria'] = request.form['kategoria']
        session['euro'] = request.form['euro']
        return redirect(url_for('utvonal'))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT ev FROM dijak ORDER BY ev DESC")
    evek = [row[0] for row in c.fetchall()]
    
    kategoriak = ['Személygépkocsi', 'Motorkerékpár', 'Autóbusz', 'Tehergépkocsi']  # szükség szerint bővíthető
    euro_osztalyok = ['EURO 0', 'EURO 1', 'EURO 2', 'EURO 3', 'EURO 4', 'EURO 5', 'EURO 6']
    
    conn.close()
    return render_template('params.html', evek=evek, kategoriak=kategoriak, euro_osztalyok=euro_osztalyok)

@app.route('/utvonal', methods=['GET', 'POST'])
def utvonal():
    if 'ev' not in session:
        return redirect(url_for('params'))
    
    if request.method == 'POST':
        coords = request.json['coords']  # [[lon, lat], ...]
        dij = szamol_dij(session['kategoria'], session['euro'], session['ev'], coords)
        return jsonify({'dij': dij})
    
    return render_template('utvonal.html',
                           kategoria=session['kategoria'],
                           euro=session['euro'],
                           ev=session['ev'])

if __name__ == '__main__':
    app.run(debug=True)