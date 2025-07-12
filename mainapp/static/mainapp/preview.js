import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

let axesHelper = null;
let gridHelper = null;
let htmlLabels = {};
let labelsContainer = null;
let scaleContainer = null;
let gridSize = 100;
let boundingBox = {x: 100, y:100, z:100};
let groundPosition = 0;

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

	const renderer = new THREE.WebGLRenderer({ antialias: true });
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
		'controls': controls,
		'renderPane': renderPane,
	}
}

function loadGLB(url, options, three) {
	const loader = new GLTFLoader();

	loader.load(url, function(gltf) {
		const scene = three.scene;
		const camera = three.camera;
		const renderer = three.renderer;
		const controls = three.controls;
		const renderPane = three.renderPane;

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
		boundingBox = size;
		groundPosition = -size.y/2 - bbox.min.y;

		object.position.sub(center);

		const maxDim = Math.max(size.x, size.y, size.z);
		const fov = camera.fov * (Math.PI / 180);
		const cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
		camera.position.set(center.x, center.y, cameraZ * 1.5);
		camera.lookAt(new THREE.Vector3(0, 0, 0));

		gridSize = maxDim;

		let mixer = null;
	
		if (gltf.animations && gltf.animations.length > 0) {
			mixer = new THREE.AnimationMixer(object);
			gltf.animations.forEach((clip) => {
				mixer.clipAction(clip).play();
			});
		}

		setupFullscreenButton(three);

		animate(renderer, scene, camera, controls, options, mixer, renderPane);
	}, undefined, function(error) {
		console.error("Error loading GLB:", error);
	});
}

function animate(renderer, scene, camera, controls, options, mixer, renderPane) {
	// clock instance needs to be outside the animation
	// loop to ensure consistency with the mixer 
	const clock = new THREE.Clock();

	function loop() {
		requestAnimationFrame(loop);

		const delta = clock.getDelta();

		if (mixer) mixer.update(delta);

		resizeCanvas(renderer, camera, options, renderPane);

		controls.update();

		if (document.fullscreenElement) {
			updateLabels(camera);
		}

		renderer.render(scene, camera);
	}

	loop();
}


function resizeCanvas(renderer, camera, options, renderPane) {
	const canvas = renderer.domElement;

	canvas.style = null;
	let width, height;
	if (document.fullscreenElement === renderPane) {
		width = window.innerWidth; 
		height = window.innerHeight;
	} else {
		width = options['width'];
		height = options['height'];
	}

	if(canvas.width != width || canvas.height != height) {
		renderer.setSize(width, height, false);
		camera.aspect = width/height;
		camera.updateProjectionMatrix();
	}
}

function toggleVisualHelpers(scene, enable) {
	if (enable) {
	if (!axesHelper) {
			axesHelper = new THREE.AxesHelper(gridSize/2);
			axesHelper.position.y = groundPosition;
			scene.add(axesHelper);
		}

		if (!gridHelper) {
			gridHelper = new THREE.GridHelper(gridSize);
			gridHelper.position.y = groundPosition;
			scene.add(gridHelper);
		}

		labelsContainer = document.getElementById('labels-container');
		if (labelsContainer) {
			labelsContainer.style.display = 'block';
			if (Object.keys(htmlLabels).length === 0) {
				labelsContainer = document.getElementById('labels-container');
				if (!labelsContainer) return;

				labelsContainer.innerHTML = '';
				htmlLabels = {};

				htmlLabels.x = createLabelElement('X', 'red');
				htmlLabels.y = createLabelElement('Y', 'green');
				htmlLabels.z = createLabelElement('Z', 'blue');
				labelsContainer.appendChild(htmlLabels.x);
				labelsContainer.appendChild(htmlLabels.y);
				labelsContainer.appendChild(htmlLabels.z);
			}
		}

		scaleContainer = document.getElementById('scale-container');
		if (scaleContainer) {
			scaleContainer.style.display = 'block';
			if (!gridSize) return;

			const gridSpacing = gridSize / 10;
			const totalSize = boundingBox.x * boundingBox.y * boundingBox.z;
			
			const gridSizeEl = document.getElementById('grid-size-value');
			const gridSpacingEl = document.getElementById('grid-spacing-value');
			const squareSizeEl = document.getElementById('square-size-value');
			const modelSpaceEl = document.getElementById('model-space-value');
			
			if (gridSizeEl) gridSizeEl.textContent = `${gridSize.toFixed(1)}m`;
			if (gridSpacingEl) gridSpacingEl.textContent = `${gridSpacing.toFixed(1)}m`;
			if (squareSizeEl) squareSizeEl.textContent = `${gridSpacing.toFixed(1)}m × ${gridSpacing.toFixed(1)}m`;
			if (modelSpaceEl) modelSpaceEl.innerHTML = `${totalSize.toFixed(0)}m<sup>3</sup>`;
		}
	} else {
		if (axesHelper) {
			scene.remove(axesHelper);
			axesHelper.dispose();
			axesHelper = null;
		}

		if (gridHelper) {
			scene.remove(gridHelper);
			gridHelper.dispose();
			gridHelper = null;
		}

		if (labelsContainer) {
			labelsContainer.style.display = 'none';
		}

		if (scaleContainer) {
			scaleContainer.style.display = 'none';
		}
	}
}

function createLabelElement(text, color) {
	const div = document.createElement('div');
	div.className = 'axis-label';
	div.style.color = color;
	div.textContent = text;
	return div;
}

function updateLabels(camera) {
	if (!labelsContainer || labelsContainer.style.display === 'none' || !camera) return;

	const tempV = new THREE.Vector3();
	const label3DPositions = {
		x: new THREE.Vector3(gridSize/2, groundPosition, 0),
		y: new THREE.Vector3(0, gridSize/2 + groundPosition, 0),
		z: new THREE.Vector3(0, groundPosition, gridSize/2),
	};

	for (const axis in {x:true, y:true, z:true}) {
		const label = htmlLabels[axis];
		const position = label3DPositions[axis];

		tempV.copy(position);
		tempV.project(camera);

		const x = (tempV.x * 0.5 + 0.5) * window.innerWidth;
		const y = (-tempV.y * 0.5 + 0.5) * window.innerHeight;

		label.style.left = `${x}px`;
		label.style.top = `${y}px`;
	}

}

function handleFullscreenChange(threeInstance) {
	const renderPane = document.querySelector('.render-pane');
	const isFullscreen = document.fullscreenElement === renderPane;

	if (isFullscreen) {
		console.log('Entered fullscreen for render-pane');
		toggleVisualHelpers(threeInstance.scene, true);
	} else {
		console.log('Exited fullscreen for render-pane');
		toggleVisualHelpers(threeInstance.scene, false);
	}
	
	resizeCanvas(threeInstance.renderer, threeInstance.camera, {}, renderPane);
}

function setupFullscreenButton(threeInstance) {
	const fullscreenButton = document.getElementById('fullscreen-button');
	if (!fullscreenButton) return;

	fullscreenButton.addEventListener('click', function (event) {
		const renderPane = document.querySelector('.render-pane');

		if (!document.fullscreenElement && renderPane.requestFullscreen) {
			renderPane.requestFullscreen();
		} else if (document.exitFullscreen) {
			document.exitFullscreen();
		}
	});

	document.addEventListener('fullscreenchange', function (event) {
		handleFullscreenChange(threeInstance);
	});
}

window.setUpRenderPane = setUpRenderPane;
window.displayPreview = displayPreview;
