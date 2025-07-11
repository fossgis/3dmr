import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

function setUpStats() {
    const elems = document.querySelectorAll('div.render-pane');

	for(const elem of elems) {
		const model_id = elem.dataset.model;
		const revision = elem.dataset.revision;
        const url = "/api/model/" + model_id + "/" + revision;
        
        initTHREE(url);
	}
}

function initTHREE(fileURL) {
    const loader = new GLTFLoader();

    loader.load(
        fileURL,
        function (gltf) {
            document.getElementById("model-status").style.display = "none";
            processModel(gltf);
        },
        function (progress) {
            const percent = progress.total > 0
                ? (progress.loaded / progress.total * 100).toFixed(1)
                : "0";
            document.getElementById("model-preview").style.display = "block";
            document.getElementById("model-status").textContent =
                `Loading model... ${percent}%`;
        },
        function (error) {
            console.error("Error loading model:", error);
            document.getElementById("model-status").textContent = "Error loading model: " + error.message;
            document.getElementById("model-status").style.display = "block";
            document.getElementById("model-preview").style.display = "none";
        }
    );
}

function processModel(gltf) {
    const stats = calculateModelStats(gltf.scene, gltf.animations);
    updateModelStats(stats);
}

function calculateModelStats(model, animations) {
    let faceCount = 0;
    let meshCount = 0;

    const seenMaterials = new Set();
    const seenTextures = new Set();
    const boundingBox = new THREE.Box3().setFromObject(model);

    model.traverse(function (child) {
        if (child.isMesh) {
            meshCount++;
        }
        if (child.isMesh && child.geometry) {
            if (child.geometry.index) {
                faceCount += child.geometry.index.count / 3;
            } else if (child.geometry.attributes.position) {
                faceCount += child.geometry.attributes.position.count / 3;
            }
        }
        if (child.isMesh && child.material){
            const materials = Array.isArray(child.material)
                ? child.material
                : [child.material];
            materials.forEach((mat) => {
                seenMaterials.add(mat.uuid);

                const textures = [
                    'metalnessMap',
                    'roughnessMap',
                    'normalMap',
                    'aoMap',
                    'map',
                    'emissiveMap',
                    'bumpMap',
                    'displacementMap',
                    'alphaMap',
                    'envMap',
                    'clearcoatMap',
                    'clearcoatRoughnessMap',
                    'clearcoatNormalMap',
                    'sheenColorMap',
                    'specularMap'
                ];

                textures.forEach(slot => {
                    const tex = mat[slot];
                    if (tex && tex.isTexture) {
                        seenTextures.add(tex.uuid);
                    }
                });
            });
        }
    });

    const size = boundingBox.getSize(new THREE.Vector3());

    const hasAnimations = Array.isArray(animations) && animations.length > 0;
    const triangleDensity = faceCount / (size.x * size.y * size.z || 1);

    return {
        faces: Math.floor(faceCount),
        volume: size.x * size.y * size.z,
        triangleDensity: triangleDensity.toFixed(2),

        boundingBox: {
            width: size.x.toFixed(2),
            height: size.y.toFixed(2),
            depth: size.z.toFixed(2)
        },
        visualDetailScore: seenMaterials.size + (1.5 * seenTextures.size),
        meshes: meshCount,
        hasAnimations,
    };
}

function setStatQualityClass(id, quality) {
    const el = document.getElementById(id);
    if (!el) return;

    const classMap = {
        good: "text-success",
        warning: "text-warning",
        bad: "text-danger",
        neutral: "text-muted"
    };
    el.classList.remove(...Object.values(classMap));

    if (quality && classMap[quality]) {
        el.classList.add(classMap[quality]);
    }
}

function updateModelStats(stats) {
    const fc = stats.faces;
    // toLocaleStrinng produces inconsistent decimal seperators across different regions
    document.getElementById("faceCount").textContent = fc.toLocaleString();
    setStatQualityClass("faceCount", 
        fc <= 5000 ? "good" :
        fc <= 100000 ? "warning" : "bad"
    );

    const score = stats.visualDetailScore;
    document.getElementById("visualDetailScore").textContent = score.toLocaleString();
    setStatQualityClass("visualDetailScore", 
        score === 0 ? "bad" :
        score <= 5 ? "warning" : "good"
    );

    const mesh = stats.meshes;
    document.getElementById("meshCount").textContent = mesh.toLocaleString();
    setStatQualityClass("meshCount", mesh >= 1 ? "good" : "bad");

    const density = stats.triangleDensity;
    document.getElementById("triangleDensity").innerHTML = density.toLocaleString() + " triangles/meter<sup>3</sup>";
    setStatQualityClass("triangleDensity", 
        density > 0 && density <= 500 ? "good" :
        density <= 1000 ? "warning" : "bad"
    );

    document.getElementById("boundingBox").textContent =
        `${stats.boundingBox.width} meters × ${stats.boundingBox.height} meters × ${stats.boundingBox.depth} meters`;
    const volume = stats.volume;
    setStatQualityClass("boundingBox", 
        volume > 0.01 ? "good" :
        volume > 0.001 ? "warning" : "bad"
    );

    document.getElementById("hasAnimations").textContent = stats.hasAnimations ? "Yes" : "No";
    setStatQualityClass("hasAnimations", stats.hasAnimations ? "good" : "neutral");

}

window.initStatsTHREE = initTHREE;
window.setUpStats = setUpStats;
