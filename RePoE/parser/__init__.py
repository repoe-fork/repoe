from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.shared.cache import AbstractFileCache


class Parser_Module:
    file_system: FileSystem
    data_path: str
    relational_reader: RelationalReader
    caches: dict[type, AbstractFileCache] = {}
    language: str

    def __init__(
        self,
        file_system: FileSystem,
        data_path: str,
        relational_reader: RelationalReader,
        language: str,
    ) -> None:
        self.file_system = file_system
        self.data_path = data_path
        self.language = language
        self.relational_reader = relational_reader

    def get_cache(self, cache_type: type) -> AbstractFileCache:
        if cache_type not in self.caches:
            self.caches[cache_type] = cache_type(self.file_system)
        return self.caches[cache_type]

    def write(self) -> None:
        """method which writes json files to data_path"""
        raise NotImplementedError
