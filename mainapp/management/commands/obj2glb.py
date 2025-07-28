import os
import subprocess
import zipfile
from pathlib import Path
import shutil
import logging

from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Extracts .zip archives with OBJ files and converts them to .glb using obj2gltf"

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Remove extracted temporary files after conversion'
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.MODEL_DIR)
        extracted_dir = base_dir / "extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        zip_files = base_dir.rglob("*.zip")

        if not zip_files:
            logger.info("No zip files found in the model directory.")
            return

        for zip_path in zip_files:
            dir_path = zip_path.parent
            model_id = dir_path.name
            revision = zip_path.stem
            workdir = extracted_dir / f"{model_id}_{revision}"
            workdir.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Extracting {zip_path} -> {workdir}")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(workdir)
            except zipfile.BadZipFile:
                logger.error(f"Bad zip file: {zip_path}")
                continue

            obj_files = list(workdir.glob("*.obj"))
            if not obj_files:
                logger.warning(f"No OBJ file found in {zip_path} — skipping.")
                continue

            obj_file = obj_files[0]
            output_path = dir_path / f"{revision}.glb"

            logger.debug("Converting...")
            try:
                subprocess.run(
                    [
                        "npx",
                        "obj2gltf",
                        "-i", str(obj_file),
                        "-o", str(output_path),
                        "-b",
                        "--y"
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"Done: {output_path}")
            except FileNotFoundError:
                logger.error("npx command not found. Make sure npm and nodejs are installed.")
                break
            except subprocess.CalledProcessError as e:
                logger.error(f"Conversion failed for {zip_path}")
                logger.info(f"Command: {' '.join(e.cmd)}")
                logger.info(f"Exit code: {e.returncode}")
                logger.info("--- stdout ---")
                logger.info(e.stdout)
                logger.error("--- stderr ---")
                logger.error(e.stderr)
            if (options['cleanup']):
                zip_path.unlink()
                logger.info(f"Removed {zip_path}")
        
        if len(os.listdir(extracted_dir)):
            shutil.rmtree(extracted_dir)
            logger.info(f"Removed {extracted_dir}")
