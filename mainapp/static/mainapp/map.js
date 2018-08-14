var map;

function rangeSearch(latitude, longitude, range, callback, page) {
	var xhr = new XMLHttpRequest();
	xhr.addEventListener("load", function() {
		callback(JSON.parse(xhr.responseText));
	});

	xhr.open("POST", "/api/search/full");

	var requestBody = 
		'{' +
		'"lat":' + latitude + ',' +
		'"lon":' + longitude + ',' +
		'"range":' + range + ',' +
		'"page":' + page + ',' +
		'"format": ["id", "title", "latitude", "longitude"]' +
		'}';

	xhr.send(requestBody);
}

var model_ids = new Set();
var page = 1;
function queryModels(response) {
	if(typeof response !== 'undefined') {
		if(response.length == 0)
			return;
		else for(var i in response) {
			var model = response[i];
			var model_id = model[0];

			if(model_ids.has(model_id))
				continue;

			var title = model[1];
			var latitude = model[2];
			var longitude = model[3];

			addPin({
				id: model_id,
				title: title,
				lat: latitude,
				lon: longitude
			});
		}
	}

	var center = map.getCenter();

	var bounds = map.getBounds();
	var corner = bounds.getNorthEast();

	var distance = map.distance(center, corner);

	rangeSearch(center.lat, center.lng, distance, queryModels, page);
	page++;
}

function addPin(model) {
	var latitude = model["lat"];
	var longitude = model["lon"];

	L.marker([latitude, longitude])
		.bindPopup('<a href="/model/' + model["id"] + '">' + model["title"] + '</a>')
		.addTo(map);

	model_ids.add(model["id"]);
}

function initMap(id, latitude, longitude, width, height) {
	map = L.map(id, {
		'worldCopyJump': true,
		'zoom': 17
	});

	if(width && height) {
		map.getSize = function() {
			return L.point(width, height);
		};
	}

	map.setView([latitude, longitude]);

	L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
		attribution: 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
		minZoom: 3,
		maxZoom: 18
	}).addTo(map);

	map.on("moveend", function() {
		page = 1;
		queryModels();

	});

	queryModels();
}
