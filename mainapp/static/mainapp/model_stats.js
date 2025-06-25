import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

function initTHREE(fileURL) {
    const loader = new GLTFLoader();

    loader.load(
        fileURL,
        function (gltf) {
            console.log("Model loaded successfully:", gltf.scene);
            if (document.getElementById("model-status")){
                document.getElementById("model-status").style.display = "none";
            }
            processModel(gltf);
        },
        function (progress) {
            const percent = progress.total > 0
                ? (progress.loaded / progress.total * 100).toFixed(1)
                : "0";
            if (document.getElementById("model-status")){
                document.getElementById("model-content").style.display = "block";
                document.getElementById("model-status").textContent =
                    `Loading model... ${percent}%`;
            }
        },
        function (error) {
            console.error("Error loading model:", error);
            if (document.getElementById("model-status")){
                document.getElementById("model-status").textContent = "Error loading model: " + error.message;
                document.getElementById("model-status").style.display = "block";
                document.getElementById("model-content").style.display = "none";
            }
        }
    );
}

function processModel(gltf) {
    const stats = calculateModelStats(gltf.scene, gltf.animations);
    updateModelStats(stats);
}

function calculateModelStats(model, animations) {
    let vertexCount = 0;
    let faceCount = 0;
    let meshCount = 0;
    let materialCount = 0;
    const seenMaterials = new Set();
    const boundingBox = new THREE.Box3().setFromObject(model);

    model.traverse(function (child) {
        if (child.isMesh) {
            meshCount++;
        }
        if (child.isMesh && child.geometry) {
            if (child.geometry.attributes.position) {
                vertexCount += child.geometry.attributes.position.count;
            }
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
                if (!seenMaterials.has(mat.uuid)) {
                    seenMaterials.add(mat.uuid);
                    materialCount += 1;
                }
            });
        }
    });

    const size = boundingBox.getSize(new THREE.Vector3());

    // we will need to enforce scale=1
    const scale = model.scale;
    const hasAnimations = Array.isArray(animations) && animations.length > 0;
    const triangleDensity = faceCount / (size.x * size.y * size.z || 1);

    return {
        vertices: Math.floor(vertexCount),
        faces: Math.floor(faceCount),
        volume: size.x * size.y * size.z,
        triangleDensity: triangleDensity.toFixed(2),

        boundingBox: {
            width: size.x.toFixed(2),
            height: size.y.toFixed(2),
            depth: size.z.toFixed(2)
        },
        scale: {
            x: scale.x.toFixed(2),
            y: scale.y.toFixed(2),
            z: scale.z.toFixed(2)
        },

        materials: materialCount,
        meshes: meshCount,
        hasAnimations,
    };
}

function setStatQualityClass(id, quality) {
    const el = document.getElementById(id);
    if (!el) return;

    const classList = ["stat-good", "stat-warning", "stat-bad", "stat-neutral"];
    el.classList.remove(...classList);

    if (quality && classList.includes("stat-" + quality)) {
        el.classList.add("stat-" + quality);
    }
}

function updateModelStats(stats) {
    const vc = stats.vertices;
    document.getElementById("vertexCount").textContent = vc.toLocaleString();
    setStatQualityClass("vertexCount", 
        vc >= 300 ? "good" :
        vc >= 100 ? "warning" : "bad"
    );

    const fc = stats.faces;
    document.getElementById("faceCount").textContent = fc.toLocaleString();
    setStatQualityClass("faceCount", 
        fc >= 200 ? "good" :
        fc >= 50 ? "warning" : "bad"
    );

    const mc = stats.materials;
    document.getElementById("materialCount").textContent = mc.toLocaleString();
    setStatQualityClass("materialCount", mc >= 1 ? "good" : "bad");

    const mesh = stats.meshes;
    document.getElementById("meshCount").textContent = mesh.toLocaleString();
    setStatQualityClass("meshCount", mesh >= 1 ? "good" : "bad");

    const density = stats.triangleDensity;
    document.getElementById("triangleDensity").textContent = density.toLocaleString();
    setStatQualityClass("triangleDensity", 
        density > 0 && density <= 500 ? "good" :
        density <= 1000 ? "warning" : "bad"
    );

    const scale = stats.scale;
    document.getElementById("modelScale").textContent =
        `${scale.x} × ${scale.y} × ${scale.z}`;
    const isScaleOk = 
        Math.abs(scale.x - 1) <= 0.05 &&
        Math.abs(scale.y - 1) <= 0.05 &&
        Math.abs(scale.z - 1) <= 0.05;
    setStatQualityClass("modelScale", isScaleOk ? "good" : "warning");

    document.getElementById("boundingBox").textContent =
        `${stats.boundingBox.width} × ${stats.boundingBox.height} × ${stats.boundingBox.depth}`;
    const volume = stats.volume;
    setStatQualityClass("boundingBox", 
        volume > 0.01 ? "good" :
        volume > 0.001 ? "warning" : "bad"
    );

    document.getElementById("hasAnimations").textContent = stats.hasAnimations ? "Yes" : "No";
    setStatQualityClass("hasAnimations", stats.hasAnimations ? "good" : "neutral");

}

window.initStatsTHREE = initTHREE;