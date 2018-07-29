// zip lib, path for other source files
zip.workerScriptsPath = "/static/mainapp/lib/";

function displayPreview(elementId, model_id, revision, options) {
	var url = "/api/model/" + model_id + "/" + revision;

	if(typeof options === 'undefined')
		options = {};

	var three = initTHREE(elementId, options);
	loadObjFromZip(url, options, three, onLoad);
}

function initTHREE(elementId, options) {
	var renderPane = document.getElementById(elementId);

	if(typeof options['width'] === 'undefined')
		options['width'] = renderPane.clientWidth;

	if(typeof options['height'] === 'undefined')
		options['height'] = renderPane.clientHeight;

	var renderer = new THREE.WebGLRenderer();

	renderPane.appendChild(renderer.domElement);

	var scene = new THREE.Scene();
	scene.background = new THREE.Color(0x87cefa);

	var camera = new THREE.PerspectiveCamera(75, options['width'] / options['height'], 0.1, 1000);
	resizeCanvas(renderer, camera, options);

	var controls = new THREE.OrbitControls(camera, renderer.domElement);

	var light = new THREE.AmbientLight(0xffffff);
	scene.add(light);

	renderer.render(scene, camera);

	return {
		'scene': scene,
		'camera': camera,
		'renderer': renderer,
		'controls': controls
	}
}

function loadObjFromZip(url, options, three, callback) {
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
					callback(objText, mtlText, textures, options, three);
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
	}, function(e) {
		// zip.createReader on error
		if(e && e.target && e.target.getAllResponseHeaders) {
			// if abort is truthy, then the user aborted the downloading.
			var abort = !e.target.getAllResponseHeaders();

			if(abort) return;
		}

		var scene = three['scene'];
		var camera = three['camera'];
		var renderer = three['renderer'];
		var controls = three['controls'];
		scene.background = new THREE.Color(0xed4337);

		animate(renderer, scene, camera, controls, options);
	});
}


function onLoad(objText, mtlText, textures, options, three) {
	var scene = three['scene'];
	var camera = three['camera'];
	var renderer = three['renderer'];
	var controls = three['controls'];

	var mtlLoader = new THREE.MTLLoader();
    mtlLoader.setMaterialOptions({
        side: THREE.DoubleSide
    });
	var materialCreator = mtlLoader.parse(mtlText);

	// turn each loaded texture from the material definitions
	// into the proper URL we got from the zip blobs
	var materialsInfo = materialCreator.materialsInfo;
	for(var i in materialsInfo) {
		var material = materialsInfo[i];

		if(!material.map_kd)
			continue;

		var splits = material.map_kd.split(/[\/]/);
		var filename = splits[splits.length - 1];

		material.map_kd = textures[filename];
	}

	materialCreator.preload();

	var objLoader = new THREE.OBJLoader();
	objLoader.setMaterials(materialCreator);
	var object = objLoader.parse(objText);

	for(var i in object.children) {
		var mesh = object.children[i];

		if(mesh.type != 'LineSegments')
			continue;

		if(!mesh.material)
			continue;

		mesh.material.lights = false;
	}

	scene.add(object);

	var bbox = new THREE.Box3().setFromObject(object);

	object.position.x = -(bbox.min.x + bbox.max.x)/2;
	object.position.y = -(bbox.min.y + bbox.max.y)/2;
	object.position.z = -(bbox.min.z + bbox.max.z)/2;

	var difX = bbox.max.x - bbox.min.x;
	var difY = bbox.max.y - bbox.min.y;
	var difZ = bbox.max.z - bbox.min.z;

	var cameraDistanceFactor = 0.9;
	camera.position.x = object.position.x + difX * cameraDistanceFactor;
	camera.position.y = object.position.y + difY * cameraDistanceFactor;
	camera.position.z = object.position.z + difZ * cameraDistanceFactor;

	var cameraLookAt = new THREE.Vector3(0, 0, 0);
	camera.lookAt(cameraLookAt);

	animate(renderer, scene, camera, controls, options);
}

function animate(renderer, scene, camera, controls, options) {
	requestAnimationFrame(function() {
		animate(renderer, scene, camera, controls, options);
	});

	resizeCanvas(renderer, camera, options);
	controls.update();

	renderer.render(scene, camera);
}

function resizeCanvas(renderer, camera, options) {
	var canvas = renderer.domElement;

	var width = options['width'];
	var height = options['height'];

	if(canvas.width != width || canvas.height != height) {
		renderer.setSize(width, height, false);
		camera.aspect = width/height;
		camera.updateProjectionMatrix();
	}
}

function setupRenderPanes() {
	var elems = document.querySelectorAll('div.render-pane');

	for(var elem of elems) {
		var properties = elem.id.match(/render-pane(\d+).(\d+)/);
		displayPreview(elem.id, properties[1], properties[2]);
	}
}

setupRenderPanes();
