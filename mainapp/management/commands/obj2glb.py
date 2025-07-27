import os
import subprocess
import zipfile
from pathlib import Path
import shutil

from django.core.management.base import BaseCommand
from django.conf import settings

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

        for zip_path in zip_files:
            dir_path = zip_path.parent
            model_id = dir_path.name
            revision = zip_path.stem
            workdir = extracted_dir / f"{model_id}_{revision}"
            workdir.mkdir(parents=True, exist_ok=True)

            self.stdout.write(f"Extracting {zip_path} -> {workdir}")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(workdir)
            except zipfile.BadZipFile:
                self.stderr.write(f"Bad zip file: {zip_path}")
                continue

            obj_files = list(workdir.glob("*.obj"))
            if not obj_files:
                self.stdout.write(f"No OBJ file found in {zip_path} — skipping.")
                continue

            obj_file = obj_files[0]
            output_path = dir_path / f"{revision}.glb"

            self.stdout.write(f"Converting...")
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
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.stdout.write(f"Done: {output_path}")
            except FileNotFoundError:
                self.stderr.write("npx command not found. Make sure npm and nodejs are installed.")
                break
            except subprocess.CalledProcessError:
                self.stderr.write(f"Conversion failed for {zip_path}")
            if (options['cleanup']):
                zip_path.unlink()
                self.stdout.write(f"Removed {zip_path}")
        
        if len(os.listdir(extracted_dir)):
            shutil.rmtree(extracted_dir)
            self.stdout.write(f"Removed {extracted_dir}")
