import re
from dataclasses import dataclass

from PyPoE.poe.file.shared import AbstractFile, ParserError


class ARMFile(AbstractFile):
    _re_version = re.compile(r"^version ([0-9]+)$")
    _re_data = re.compile(r'^(?P<key>\S+):\s+(?P<value>.*)|"(?P<string>.*)"|(?P<number>\d+)$')
    _re_token = re.compile(
        r'^(?:(?P<int>-?\d+)|(?P<float>-?\d*\.\d+)|"(?P<quoted>(?:[^"]|\\")*)"|(?P<word>\S+))\s*(?P<rest>.*)$'
    )
    _re_cell = re.compile(r"^\s*(?P<tag>[kfson])(?P<data>(\s+-?\d+)*)(?P<rest>\s+[kfson].*)?\s*$")

    __slots__ = (
        "version",
        "overrides",
        "strings",
        "dims",
        "numbers",
        "tag",
        "pois",
        "doodads",
        "grid",
        "root_slot",
        "sequel",
    )

    _REPR_EXTRA_ATTRIBUTES = {x: None for x in __slots__}

    def __init__(self, filename="<unknown>", sequel=1):
        super().__init__()
        self.filename = filename
        self.sequel = sequel
        self.overrides = None

    def _read(self, buffer, *args, **kwargs):
        lines = [line for line in buffer.read().decode("utf-16").splitlines() if line.strip()]

        version = self._re_version.match(lines.pop(0))
        if not version:
            raise ParserError(f"{self} - Failed to find version. File may not be a .dgr file or malformed.")
        self.version = int(version.group(1))

        string_count = int(lines.pop(0))
        self.strings = [self.quoted_string(l) for l in lines[:string_count]]

        lines[:] = lines[string_count:]

        self.dims = self.number_list(lines.pop(0))
        self.numbers = [self.number_list(lines.pop(0))]
        self.tag = self.quoted_string(lines.pop(0))
        self.numbers.append(self.number_list(lines.pop(0)))
        self.root_slot, rest = self.grid_cell(lines.pop(0))
        if rest:
            raise ParserError(f"{self} - Unexpected data after root slot: {rest}.")
        self.numbers.extend(self.number_list(lines.pop(0)) for _ in range(sum(self.numbers[0]) * 2))

        self.pois = self.points_of_interest(lines)
        self.grid = [self.grid_row(lines.pop(0)) for _ in range(self.root_slot.height)]
        self.doodads = self.points_of_interest(lines)

    def grid_row(self, line):
        result = []
        for _ in range(self.root_slot.width):
            cell, line = self.grid_cell(line)
            result.append(cell)
        if line:
            raise ParserError(f"{self} - Unexpected data after reading grid row: {line}.")
        return result

    def grid_cell(self, line: str):
        match = self._re_cell.match(line)
        if not match:
            raise ParserError(f"{self} - Unexpected cell format: '{line}'")
        if match.group("tag") == "k":
            return Slot(match.group("tag"), match.group("data"), self), match.group("rest")
        elif match.group("tag") == "f":
            return Fill(match.group("tag"), self.get_string(int(match.group("data").strip()))), match.group("rest")
        elif match.group("tag") == "s":
            return Static(match.group("tag")), match.group("rest")
        elif match.group("tag") == "o":
            return Open(match.group("tag")), match.group("rest")
        elif match.group("tag") == "n":
            return Null(match.group("tag")), match.group("rest")
        else:
            raise ParserError(f"{self} - Unexpected cell tag: {match.group('tag')} in {line}.")

    def points_of_interest(self, lines: list[str]):
        result = []
        group = []
        while lines:
            line = lines.pop(0)
            parsed = self.tokenise(line)
            if len(parsed) == 1:
                if isinstance(parsed[0], str):
                    result.append(group)
                    if parsed[0]:
                        self.overrides = parsed[0]
                    return result
                count = parsed[0]
                if count >= 0:
                    if group:
                        raise ParserError(
                            f"{self} - Mixed array styles, found separator: {parsed} while holding {group}."
                        )
                    if len(lines) < count:
                        count = len(lines)
                    result.append([self.tokenise(lines.pop(0)) for _ in range(count)])
                else:
                    if count != -1:
                        raise ParserError(f"{self} - Unexpected negative count: {count}.")
                    result.append(group)
                    group = []
            elif isinstance(parsed[0], str) and len(parsed[0]) == 1:
                if group:
                    raise ParserError(f"{self} - Hit grid {parsed} row with group still in progress {group}.")
                lines.insert(0, line)
                return result
            else:
                # poe2-style group should be followed by a -1
                group.append(parsed)
        if group:
            if lines:
                raise ParserError(f"{self} - Unterminated group {group}.")
            result.append(group)
        return result

    def tokenise(self, line):
        result = []
        rest = line
        while rest:
            match = self._re_token.match(rest)
            if not match:
                raise ParserError(f"{self} - Unexpected value in {line}\n at {rest}")
            if match.group("int") is not None:
                result.append(int(match.group("int")))
            elif match.group("float") is not None:
                result.append(float(match.group("float")))
            elif match.group("word") is not None:
                result.append(match.group("word"))
            else:
                quoted = match.group("quoted")
                result.append(quoted)
                if '"' in quoted or "\\\\" in quoted:
                    # Assume that backslash-escapes work as one would expect? Nah let's throw it up
                    raise ParserError(f'{self} - Possible backslash-escape found in "{quoted}"')
            rest = match.group("rest")

        return result

    def quoted_string(self, string: str):
        if string[0] != '"' or string[-1] != '"':
            raise ParserError(f"{self} - Expected quoted string, got {string}")
        quoted = string[1:-1]
        if '"' in quoted or "\\\\" in quoted:
            # Assume that backslash-escapes work as one would expect? Nah let's throw it up
            raise ParserError(f'Possible backslash-escape found in "{quoted}"')
        return quoted

    @staticmethod
    def number_list(string: str):
        return [int(n) for n in string.split()]

    def get_string(self, idx: int):
        if not idx:
            return None
        if idx > len(self.strings):
            raise ParserError(f"{self} - String index {idx} out of bounds.")
        return self.strings[idx - 1]

    def to_dict(self):
        return {slot: getattr(self, slot) for slot in self.__slots__ if slot != "sequel"}


@dataclass
class Cell:
    def __init__(self, tag, expected):
        if tag != expected:
            raise ParserError(f"Expected tag '{expected}', but was '{tag}'")
        self.tag = tag
        self.width = 1
        self.height = 1


@dataclass
class Slot(Cell):
    def __init__(self, tag: str, data: str, parent: ARMFile):
        super().__init__(tag, "k")
        vals = [int(d) for d in data.split()]
        if len(vals) < 23:
            raise ParserError(f"{self} - Insufficient data: {data}")
        self.width = vals[0]
        self.height = vals[1]
        self.tag = parent.get_string(vals[22])
        self.anchor = ["sw", "se", "ne", "nw"][vals[23]]
        self.edges = dict(
            zip(
                ["n", "w", "s", "e"],
                [
                    {
                        "edge": parent.get_string(vals[2 + i]),
                        "exit": vals[6 + i * 2],
                        "virtual_exit": vals[7 + i * 2],
                    }
                    for i in range(4)
                ],
            )
        )
        self.corners = dict(
            zip(
                ["sw", "se", "ne", "nw"],
                [
                    {
                        "ground": parent.get_string(vals[14 + i]),
                        "height": vals[18 + i],
                    }
                    for i in range(4)
                ],
            )
        )


@dataclass
class Fill(Cell):
    def __init__(self, tag, data):
        super().__init__(tag, "f")
        self.fill = data


@dataclass
class Static(Cell):
    def __init__(self, tag):
        super().__init__(tag, "s")


@dataclass
class Open(Cell):
    def __init__(self, tag):
        super().__init__(tag, "o")


@dataclass
class Null(Cell):
    def __init__(self, tag):
        super().__init__(tag, "n")
