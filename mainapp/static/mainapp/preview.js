import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

function setUpRenderPane(){
	const elems = document.querySelectorAll('div.render-pane');

	for(const elem of elems) {
		const model_id = elem.dataset.model;
		const revision = elem.dataset.revision;
		const url = "/api/model/" + model_id + "/" + revision;

		displayPreview(elem.id, url, {}, model_id, revision,);
	}
}

function displayPreview(elementId, url, options={}) {

	const three = initTHREE(elementId, options);
	loadGLB(url, options, three);
}

function initTHREE(elementId, options) {
	const renderPane = document.getElementById(elementId);

	if(typeof options['width'] === 'undefined')
		options['width'] = renderPane.clientWidth;

	if(typeof options['height'] === 'undefined')
		options['height'] = renderPane.clientHeight;

	const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
	renderer.setPixelRatio(window.devicePixelRatio);
	renderer.setSize(options['width'], options['height']);
	renderer.outputEncoding = THREE.sRGBEncoding;
	renderer.toneMapping = THREE.ACESFilmicToneMapping;
	renderer.toneMappingExposure = 1.0;
	renderer.physicallyCorrectLights = true;
	renderer.shadowMap.enabled = true;
	renderer.shadowMap.type = THREE.PCFSoftShadowMap;

	renderPane.appendChild(renderer.domElement);

	const scene = new THREE.Scene();
	scene.background = new THREE.Color(0x87cefa);

	const camera = new THREE.PerspectiveCamera(75, options['width'] / options['height'], 0.1, 1000);
	resizeCanvas(renderer, camera, options);

	const controls = new OrbitControls(camera, renderer.domElement);

	const ambLight = new THREE.AmbientLight(0xffffff, 0.4);
	scene.add(ambLight);

	const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
	dirLight.position.set(5, 10, 7.5);
	dirLight.castShadow = true;
	dirLight.shadow.mapSize.width = 2048;
	dirLight.shadow.mapSize.height = 2048;
	dirLight.shadow.bias = -0.0001;
	scene.add(dirLight);

	const hemiLight = new THREE.HemisphereLight(0xffffff, 0x000000, 0.6);
	scene.add(hemiLight);

	const pointLight = new THREE.PointLight(0xffffff, 1, 100);
	pointLight.position.set(10, 10, 10);
	pointLight.castShadow = true;
	pointLight.shadow.mapSize.width = 2048;
	pointLight.shadow.mapSize.height = 2048;
	pointLight.shadow.camera.near = 0.5;
	pointLight.shadow.camera.far = 500;
	pointLight.shadow.camera.fov = 50;
	scene.add(pointLight);

	renderer.render(scene, camera);

	return {
		'scene': scene,
		'camera': camera,
		'renderer': renderer,
		'controls': controls
	}
}

function loadGLB(url, options, three) {
	const loader = new GLTFLoader();

	loader.load(url, function(gltf) {
		const scene = three.scene;
		const camera = three.camera;
		const renderer = three.renderer;
		const controls = three.controls;

		const object = gltf.scene;
		scene.add(object);

		object.traverse(function(child) {
			if (child.isMesh) {
				child.castShadow = true;
				child.receiveShadow = true;
			}
		});

		const bbox = new THREE.Box3().setFromObject(object);
		const center = bbox.getCenter(new THREE.Vector3());
		const size = bbox.getSize(new THREE.Vector3());

		object.position.sub(center);

		const maxDim = Math.max(size.x, size.y, size.z);
		const fov = camera.fov * (Math.PI / 180);
		const cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
		camera.position.set(center.x, center.y, cameraZ * 1.5);
		camera.lookAt(new THREE.Vector3(0, 0, 0));

		animate(renderer, scene, camera, controls, options);
	}, undefined, function(error) {
		console.error("Error loading GLB:", error);
	});
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
	const canvas = renderer.domElement;

	const width = options['width'];
	const height = options['height'];

	if(canvas.width != width || canvas.height != height) {
		renderer.setSize(width, height, false);
		camera.aspect = width/height;
		camera.updateProjectionMatrix();
	}
}

window.setUpRenderPane = setUpRenderPane;
window.displayPreview = displayPreview;
