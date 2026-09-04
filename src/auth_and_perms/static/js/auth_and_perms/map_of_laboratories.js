

(function () {
    L.Icon.Default.imagePath = leaflet_images_path;

    const map = L.map('org-map').setView([9.9, -84.1], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    window.orgMap = map;

    fetch(laboratory_geolocations_url)
        .then(function (r) {
            return r.json();
        })
        .then(function (data) {
            const bounds = [];
            data.laboratories.forEach(function (lab) {
                const marker = L.marker([lab.lat, lab.lng]).addTo(map);
                marker.bindPopup('<strong>' + lab.lab + '</strong><br>' + lab.organization);
                bounds.push([lab.lat, lab.lng]);
            });
            if (bounds.length > 0) {
                map.fitBounds(bounds, {padding: [40, 40]});
            }
        });
})();
