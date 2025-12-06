import json
import logging
import subprocess
import tempfile

from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_glb_file(file_field):
    """
    Validates a GLB file using the Khronos Group's gltf-validator CLI.

    Raises:
        ValidationError: for file type errors or internal server errors.

    Returns:
        list: A list of error dictionaries if GLB validation fails. Each dictionary
              contains 'message' and 'pointer' keys.
        None: if the file is valid.
    """

    if not file_field.name.lower().endswith(".glb"):
        raise ValidationError("Only .glb files are supported.")

    file_field.seek(0)
    header = file_field.read(4)
    if header != b"glTF":
        raise ValidationError(
            "The uploaded file does not appear to be a valid GLB file."
        )

    with tempfile.NamedTemporaryFile(suffix=".glb") as temp_file:
        for chunk in file_field.chunks():
            temp_file.write(chunk)
        temp_file.flush()

        try:
            result = subprocess.run(
                [settings.GLTF_VALIDATOR, temp_file.name, "-o"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            logger.exception(
                f"gltf-validator CLI not found at {settings.GLTF_VALIDATOR}."
            )
            raise ValidationError("Internal server error.")

        try:
            output = json.loads(result.stdout.decode("utf-8"))
        except json.JSONDecodeError:
            logger.exception("Validator returned invalid JSON output.")
            raise ValidationError("Internal server error.")

        try:
            # Ensures the model has some shape. At least a cube.
            if output["info"]["totalVertexCount"] < 3 or \
                output["info"]["totalTriangleCount"] < 1:
                raise ValidationError(
                    "GLB file must have some valid shape."
                )

            if output["issues"]["numErrors"] > 0:
                messages = []
                for message in output["issues"]["messages"]:
                    if message["severity"] == 0:  # 0 is error in khronos validator
                        messages.append({
                            "message": message["message"],
                            "pointer": message.get("pointer", "N/A")
                        })
                return messages
        except KeyError:
            logger.exception("Invalid gltf_validator output!\
                            It seems gltf_validator's 'validation.schema.json' file has been modified.")
            raise ValidationError("Internal server error.")
