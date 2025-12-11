import hashlib

def hash_file(filename):
    h = hashlib.sha256()
    with open(filename, 'rb') as file:
        while chunk := file.read(8192):
            h.update(chunk)
    return h.hexdigest()

fajl1 = "database.csv"
fajl2 = "database_2025.csv"

try:
    h1 = hash_file(fajl1)
    h2 = hash_file(fajl2)

    print(f"1. {fajl1} ujjlenyomata: {h1[:10]}...")
    print(f"2. {fajl2} ujjlenyomata: {h2[:10]}...")

    if h1 == h2:
        print("\n❌ HIBA: A KÉT FÁJL TELJESEN EGYFORMA!")
        print("   Ezért van ugyanannyi sor az adatbázisban.")
        print("   Kérlek, cseréld le a database_2025.csv tartalmát a VALÓDI 2025-ös adatokra.")
    else:
        print("\n✅ A fájlok különböznek.")
        
except FileNotFoundError:
    print("Valamelyik fájl hiányzik a mappából.")