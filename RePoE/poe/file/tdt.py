import re
import struct

from PyPoE.poe.file.shared import AbstractFile, ParserError


class TDTFile(AbstractFile):

    tag = None
    extra = (
        "version",
        "tag",
    )

    _REPR_EXTRA_ATTRIBUTES = {x: None for x in extra}

    def __init__(self, filename="<unknown>", sequel=1):
        super().__init__()
        self.filename = filename
        self.sequel = sequel

    def _read(self, buffer, *args, **kwargs):
        data = buffer.read()
        offset = 0

        self.version = struct.unpack_from("<I", data, offset=offset)[0]
        offset += 4

        string_length = struct.unpack_from("<I", data, offset=offset)[0]
        offset += 4

        self.strings = data[offset : offset + string_length * 2].decode("utf-16")
        offset += string_length * 2

        tdt = struct.unpack_from("<I", data, offset=offset)[0]
        offset += 4
        self.tdt = self.strings[tdt:].split("\x00")[0]
        if self.tdt:
            self.tag = self.strings.split("\x00")[0]
            self.rest = data[offset:]
            return
        tgt, tag = struct.unpack_from("<II", data, offset=offset)
        offset += 8
        self.tgt = self.strings[tgt:].split("\x00")[0]
        self.tag = self.strings[tag:].split("\x00")[0]
