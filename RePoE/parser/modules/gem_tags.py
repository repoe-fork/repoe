from RePoE.parser import Parser_Module
from RePoE.parser.util import write_json, call_with_default_args


class gem_tags(Parser_Module):
    def write(self) -> None:
        root = {}
        for tag in self.relational_reader["GemTags.dat64"]:
            name = tag["Tag"]
            root[tag["Id"]] = name if name != "" else None
        write_json(root, self.data_path, "gem_tags")


if __name__ == "__main__":
    call_with_default_args(gem_tags)
