from functools import cache

from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.shared.cache import AbstractFileCache
from PyPoE.poe.file.translations import TranslationFileCache


class Parser_Module:
    file_system: FileSystem
    data_path: str
    relational_reader: RelationalReader
    caches: dict[type, AbstractFileCache]
    language: str

    def __init__(
        self,
        file_system: FileSystem,
        data_path: str,
        relational_reader: RelationalReader,
        language: str,
        caches: dict[type, AbstractFileCache],
        sequel=1,
        fail_fast=False,
    ) -> None:
        self.file_system = file_system
        self.data_path = data_path
        self.language = language
        self.relational_reader = relational_reader
        self.caches = caches or {}
        self.sequel = sequel
        self.fail_fast = fail_fast

    def file_exists(self, path: str) -> bool:
        try:
            return bool(
                self.file_system.index.get_file_record(path)
                if self.file_system.index
                else self.file_system.get_file(path)
            )
        except FileNotFoundError:
            return False

    def resolve(self, base, filename):
        resolved = self.normalize(filename)
        if self.file_exists(resolved):
            return resolved
        resolved = self.normalize(base + "/" + resolved)
        if self.file_exists(resolved):
            return resolved
        return filename

    # files from ggg contain unnormalized paths
    # could fix this better further upstream, but for now just sprinkle this function around
    @staticmethod
    def normalize(filename: str) -> str:
        while "//" in filename:
            filename = filename.replace("//", "/")
        return filename.strip()

    def get_cache(self, cache_type: type) -> AbstractFileCache:
        if cache_type not in self.caches:
            if cache_type == TranslationFileCache:
                self.caches[cache_type] = cache_type(self.file_system, sequel=self.sequel)
            else:
                self.caches[cache_type] = cache_type(self.file_system)
        return self.caches[cache_type]

    def write(self) -> None:
        """method which writes json files to data_path"""
        raise NotImplementedError
