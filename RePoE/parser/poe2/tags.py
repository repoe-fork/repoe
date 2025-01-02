from RePoE.parser.util import call_with_default_args, write_json
from RePoE.parser import Parser_Module


class tags(Parser_Module):
    def write(self) -> None:
        tags = [row["Id"] for row in self.relational_reader["Tags.dat64"]]
        write_json(tags, self.data_path, "tags")


if __name__ == "__main__":
    call_with_default_args(tags)
