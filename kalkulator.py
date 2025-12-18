from db_manager import get_db_connection

def szamol_dij(kategoria, euro, ev, coords):
    # coords: lista [[lon, lat], ...] sorrendben
    conn = get_db_connection()
    c = conn.cursor()
    
    ossz_dij = 0
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i+1]
        # Távolság egyszerű haversine képlettel (km-ben)
        from math import radians, sin, cos, sqrt, atan2
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c_val = 2 * atan2(sqrt(a), sqrt(1-a))
        tavolsag_km = R * c_val
        
        # Egyszerűsített lekérdezés – valós projektedben finomítsd az útszakaszok szerint
        c.execute("""
            SELECT napi_dij FROM dijak 
            WHERE kategoria = ? AND euro_osztaly = ? AND ev = ?
        """, (kategoria, euro, ev))
        row = c.fetchone()
        napi_dij = row[0] if row else 0
        
        # Példa: napi díj / 100 km arányosítása
        dij_szakasz = (tavolsag_km / 100) * napi_dij
        ossz_dij += dij_szakasz
    
    conn.close()
    return round(ossz_dij, 2)