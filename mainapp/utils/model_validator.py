import json
import logging
import os
import subprocess
import tempfile

from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_glb_file(file_field):
    """
    Validates a GLB file using the Khronos Group's gltf-validator CLI.

    Raises:
        ValidationError: if the file is not a valid GLB or fails validation.
    """

    if not file_field.name.lower().endswith(".glb"):
        raise ValidationError("Only .glb files are supported.")

    file_field.seek(0)
    header = file_field.read(4)
    if header != b"glTF":
        raise ValidationError(
            "The uploaded file does not appear to be a valid GLB file."
        )

    try:
        file_field.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=True) as temp_file:
            for chunk in file_field.chunks():
                temp_file.write(chunk)
            temp_file.flush()

            result = subprocess.run(
                [settings.GLTF_VALIDATOR, temp_file.name, "-o"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            output = json.loads(result.stdout.decode("utf-8"))

            # Ensures the model has some shape. At least a cube.
            if output["info"]["totalVertexCount"] < 8 or \
               output["info"]["totalTriangleCount"] < 12:
                raise ValidationError(
                    "GLB file must have some valid shape."
                )

            if output["issues"]["numErrors"]:
                raise ValidationError(
                    f"GLB validation failed with {output['issues']['numErrors']} errors: {output['issues']['errors']}"
                )

    except FileNotFoundError:
        logger.exception(
            f"gltf-validator CLI not found at {settings.GLTF_VALIDATOR}."
        )
        raise ValidationError("Internal server error.")
    except json.JSONDecodeError:
        logger.exception("Validator returned invalid JSON output.")
        raise ValidationError("Internal server error.")
    except Exception as e:
        logger.exception(f"Error during GLB validation: {str(e)}")
        raise ValidationError(f"Unknown error during GLB validation.")
