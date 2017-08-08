var map;

function rangeSearch(latitude, longitude, range, callback, page) {
	var xhr = new XMLHttpRequest();
	xhr.addEventListener("load", function() {
		callback(JSON.parse(xhr.responseText));
	});
	xhr.open("GET", "/api/search/" + latitude + "/" + longitude + "/" + range + "/" + page);
	xhr.send();
}

function modelGet(model_id, callback) {
	var xhr = new XMLHttpRequest();
	xhr.addEventListener("load", function() {
		callback(JSON.parse(xhr.responseText));
	});
	xhr.open("GET", "/api/info/" + model_id);
	xhr.send();
}

var model_ids = new Set();
var page = 1;
function queryModels(response) {
	if(typeof response !== 'undefined') {
		if(response.length == 0)
			return;
		else for(var i in response) {
			var model_id = response[i];

			if(model_ids.has(model_id))
				continue

			modelGet(model_id, addPin);
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

	L.tileLayer("http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
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
