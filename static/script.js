const map = L.map('map').setView([47.0, 19.0], 7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

let markers = [];
let routeLayer = null;
let polyline = null;
let coords = [];  // [lat, lon] sorrendben a Leaflet miatt

document.getElementById('ujpont').addEventListener('click', () => {
    const container = document.getElementById('pontok');
    const div = document.createElement('div');
    div.className = 'pont';
    div.innerHTML = `<input type="text" class="telepules" placeholder="Település neve" autocomplete="off">
                     <button type="button" class="torol">Töröl</button>`;
    container.appendChild(div);
    div.querySelector('.torol').addEventListener('click', () => div.remove());
    div.querySelector('.telepules').addEventListener('blur', validateAndUpdate);
});

document.querySelectorAll('.torol').forEach(btn => {
    btn.style.display = 'inline';
    btn.addEventListener('click', (e) => e.target.parentElement.remove());
});

document.querySelectorAll('.telepules').forEach(input => {
    input.addEventListener('blur', validateAndUpdate);
});

function validateAndUpdate() {
    updateRoute();
}

async function updateRoute() {
    clearMap();
    coords = [];
    let valid = true;

    for (let input of document.querySelectorAll('.telepules')) {
        const query = input.value.trim();
        if (!query) continue;

        const resp = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', Magyarország')}`);
        const data = await resp.json();

        if (data.length > 0) {
            const loc = data[0];
            const lat = parseFloat(loc.lat);
            const lon = parseFloat(loc.lon);
            coords.push([lat, lon]);
            L.marker([lat, lon]).addTo(map).bindPopup(loc.display_name);
            input.classList.remove('invalid');
            input.classList.add('valid');
        } else {
            input.classList.remove('valid');
            input.classList.add('invalid');
            valid = false;
        }
    }

    if (coords.length >= 2 && valid) {
        const osrmCoords = coords.map(c => c[1] + ',' + c[0]).join(';');
        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${osrmCoords}?overview=full&geometries=geojson`;
        const osrmResp = await fetch(osrmUrl);
        const osrmData = await osrmResp.json();

        if (osrmData.routes) {
            const geojson = osrmData.routes[0].geometry;
            if (routeLayer) map.removeLayer(routeLayer);
            routeLayer = L.geoJSON(geojson, {color: 'red'}).addTo(map);
            map.fitBounds(routeLayer.getBounds());

            // Húzhatóvá tesszük
            routeLayer.pm.enable({ draggable: true, snappable: false });
            routeLayer.on('pm:dragend', () => {
                const newGeo = routeLayer.toGeoJSON();
                // Opcionálisan újraszámolható a coords a módosított útvonalból
            });

            document.getElementById('szamit').disabled = false;
        }
    } else {
        document.getElementById('szamit').disabled = true;
    }
}

function clearMap() {
    markers.forEach(m => map.removeLayer(m));
    if (routeLayer) map.removeLayer(routeLayer);
    markers = [];
    routeLayer = null;
}

document.getElementById('szamit').addEventListener('click', async () => {
    const serverCoords = coords.map(c => [c[1], c[0]]);  // [lon, lat] a szervernek
    const resp = await fetch('/utvonal', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({coords: serverCoords})
    });
    const data = await resp.json();
    document.getElementById('eredmeny').textContent = `Fizetendő díj: ${data.dij} Ft`;
});