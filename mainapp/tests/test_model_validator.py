import json
import subprocess
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from mainapp.utils.model_validator import validate_glb_file


def mock_validator_output(extensions_required=None, extensions_used=None, errors=None):
    info = {"totalVertexCount": 44, "totalTriangleCount": 26}
    if extensions_required is not None:
        info["extensionsRequired"] = extensions_required
    if extensions_used is not None:
        info["extensionsUsed"] = extensions_used
    messages = [
        {"severity": 0, "message": m, "pointer": "/meshes/0"} for m in (errors or [])
    ]
    output = {
        "info": info,
        "issues": {"numErrors": len(messages), "messages": messages},
    }
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(output).encode("utf-8"), stderr=b""
    )


def glb_upload():
    with open("mainapp/tests/test_files/test_model.glb", "rb") as f:
        return SimpleUploadedFile("model.glb", f.read(), content_type="model/gltf-binary")


class ValidateGlbFileExtensionTests(SimpleTestCase):
    @patch("mainapp.utils.model_validator.subprocess.run")
    def test_model_without_extensions_is_accepted(self, mock_run):
        mock_run.return_value = mock_validator_output()
        self.assertIsNone(validate_glb_file(glb_upload()))

    @patch("mainapp.utils.model_validator.subprocess.run")
    def test_model_requiring_extension_is_rejected(self, mock_run):
        mock_run.return_value = mock_validator_output(
            extensions_required=["KHR_draco_mesh_compression"],
            extensions_used=["KHR_draco_mesh_compression"],
        )
        errors = validate_glb_file(glb_upload())
        self.assertEqual(len(errors), 1)
        self.assertIn("KHR_draco_mesh_compression", errors[0]["message"])
        self.assertEqual(errors[0]["pointer"], "/extensionsRequired/0")

    @patch("mainapp.utils.model_validator.subprocess.run")
    def test_optional_extensions_are_allowed(self, mock_run):
        mock_run.return_value = mock_validator_output(
            extensions_used=["KHR_materials_unlit"],
        )
        self.assertIsNone(validate_glb_file(glb_upload()))
