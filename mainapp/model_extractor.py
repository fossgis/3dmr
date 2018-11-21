from tempfile import mkdtemp
from shutil import rmtree
from os.path import join
import os

MAX_UNCOMPRESSED_SIZE = 100e6 # 100MB

# Extracts a zipfile into a directory safely
class ModelExtractor(object):
    def __init__(self, modelzip):
        self.modelzip = modelzip 

    def __enter__(self):
        if not self.__is_model_good():
            raise ValueError('Invalid model zip file')

        obj = self.__get_obj_filename()
        if obj is None:
            raise ValueError('No obj file present in model zip')

        self.path = mkdtemp()

        try:
            self.modelzip.extractall(self.path)
        except:
            raise ValueError('Error while extracting zip file')

        return {
            'path': self.path,
            'obj': join(self.path, obj)
        }

    def __exit__(self, type, value, tb):
        rmtree(self.path, ignore_errors=True)

    def __is_model_good(self):
        total_size_uncompressed = 0

        for path in self.modelzip.namelist():
            if '..' in path or path.startswith('/'):
                return False

            info = self.modelzip.getinfo(path)

            uncompressed_size = info.file_size
            total_size_uncompressed += uncompressed_size

        return total_size_uncompressed < MAX_UNCOMPRESSED_SIZE

    def __get_obj_filename(self):
        for info in self.modelzip.infolist():
            if info.filename.endswith('.obj'):
                return info.filename

        return None
