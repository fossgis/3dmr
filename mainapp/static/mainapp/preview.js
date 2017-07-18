// zip lib, path for other source files
zip.workerScriptsPath = "/static/mainapp/lib/";

function displayPreview(elementId, width, height, model_id, revision) {
	// TODO: update to use the get model API
	var url = "/static/mainapp/models/" + model_id + "/" + revision + ".zip";

	loadObjFromZip(url, elementId, width, height, onLoad);
}

function loadObjFromZip(url, elementId, width, height, callback) {
	zip.createReader(new zip.HttpReader(url), function(reader) {
		// zip.createReader callback
		reader.getEntries(function(entries) {
			var objText;
			var mtlText;
			var textures = {};

			var counter = Object.keys(entries).length;
			function updateCounter() {
				--counter;
				if(counter == 0)
					callback(elementId, width, height, objText, mtlText, textures);
			}

			for(var i in entries) {
				var entry = entries[i];
				var name = entry.filename;
				
				if(name.endsWith(".obj"))
					entry.getData(new zip.TextWriter(), function(text) {
						objText = text;
						updateCounter();
					});
				else if(name.endsWith(".mtl"))
					entry.getData(new zip.TextWriter(), function(text) {
						mtlText = text;
						updateCounter();
					});
				else // let's assume it's a texture.
					(function(name) {
					entry.getData(new zip.BlobWriter(), function(blob) {
						textures[name] = (window.webkitURL || window.URL).createObjectURL(blob);
						updateCounter();
					});
					})(name);
			}
		});
	}, function() {
		// zip.createReader on error
		alert("Failed loading model .zip");
	});
}


function onLoad(elementId, width, height, objText, mtlText, textures) {
	var scene = new THREE.Scene();
	var camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );

	var renderer = new THREE.WebGLRenderer();

	// this is the size of the render pane
	var CANVAS_WIDTH = width;
	var CANVAS_HEIGHT = height;

	renderer.setSize(CANVAS_WIDTH, CANVAS_HEIGHT);
	scene.background = new THREE.Color(0xffffff);

	var renderPane = document.getElementById(elementId);
	renderPane.appendChild(renderer.domElement);

	var controls = new THREE.OrbitControls(camera, renderer.domElement);

	var light = new THREE.AmbientLight(0xffffff);
	scene.add(light);

	var mtlLoader = new THREE.MTLLoader();
	var materialCreator = mtlLoader.parse(mtlText);

	// turn each loaded texture from the material definitions
	// into the proper URL we got from the zip blobs
	var materialsInfo = materialCreator.materialsInfo;
	for(var i in materialsInfo) {
		var material = materialsInfo[i];

		if(!material.map_kd)
			continue;

		var splits = material.map_kd.split('/');
		var filename = splits[splits.length - 1];

		material.map_kd = textures[filename];
	}

	materialCreator.preload();

	var objLoader = new THREE.OBJLoader();
	objLoader.setMaterials(materialCreator);
	var object = objLoader.parse(objText);

	scene.add(object);

	camera.position.z = 5;

	function animate() {
		requestAnimationFrame(animate);
		controls.update();
		renderer.render(scene, camera);
	}

	animate();
}
