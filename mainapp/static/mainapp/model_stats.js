import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

function initTHREE(file) {
    const fileURL = URL.createObjectURL(file);
    const loader = new GLTFLoader();

    loader.load(
        fileURL,
        function (gltf) {
            console.log("Model loaded successfully:", gltf.scene);
            URL.revokeObjectURL(fileURL);
            document.getElementById("model-status").style.display = "none";
            processModel(gltf, file);
        },
        function (progress) {
            const percent = progress.total > 0
                ? (progress.loaded / progress.total * 100).toFixed(1)
                : "0";
            document.getElementById("model-content").style.display = "block";
            document.getElementById("model-status").textContent =
                `Loading model... ${percent}%`;
        },
        function (error) {
            console.error("Error loading model:", error);
            URL.revokeObjectURL(fileURL);
            document.getElementById("model-status").textContent = "Error loading model: " + error.message;
            document.getElementById("model-status").style.display = "block";
            document.getElementById("model-content").style.display = "none";
        }
    );
}

function processModel(gltf, file) {
    const stats = calculateModelStats(gltf.scene);
    updateModelStats(stats, file);
}

function calculateModelStats(model) {
    let vertexCount = 0;
    let faceCount = 0;
    const boundingBox = new THREE.Box3().setFromObject(model);

    model.traverse(function (child) {
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
    });

    const size = boundingBox.getSize(new THREE.Vector3());

    // we will need to enforce scale=1
    const scale = model.scale;

    return {
        vertices: Math.floor(vertexCount),
        faces: Math.floor(faceCount),
        boundingBox: {
            width: size.x.toFixed(2),
            height: size.y.toFixed(2),
            depth: size.z.toFixed(2)
        },
        scale: {
            x: scale.x.toFixed(2),
            y: scale.y.toFixed(2),
            z: scale.z.toFixed(2)
        }
    };
}

function updateModelStats(stats, file) {
    document.getElementById("vertexCount").textContent = stats.vertices.toLocaleString();
    document.getElementById("faceCount").textContent = stats.faces.toLocaleString();
    document.getElementById("fileSize").textContent = (file.size / 1024).toFixed(1) + " KB";
    document.getElementById("boundingBox").textContent =
        `${stats.boundingBox.width} × ${stats.boundingBox.height} × ${stats.boundingBox.depth}`;
    document.getElementById("modelScale").textContent =
        `${stats.scale.x} × ${stats.scale.y} × ${stats.scale.z}`;
    if (stats.scale.x !== "1.00" || stats.scale.y !== "1.00" || stats.scale.z !== "1.00") {
        document.getElementById("modelScale").style.color = "red";
    } else {
        document.getElementById("modelScale").style.color = "inherit";
    }
}

window.initStatsTHREE = initTHREE;