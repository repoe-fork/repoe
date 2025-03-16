from RePoE.parser.util import call_with_default_args, write_any_json, write_json
from RePoE.parser import Parser_Module


class keywords(Parser_Module):
    def write(self) -> None:
        keywords = {
            row["Id"]: {"term": row["Term"], "definition": row["Definition"]} for row in self.relational_reader["KeywordPopups.dat64"]
        }
        write_any_json(keywords, self.data_path, "keywords")


if __name__ == "__main__":
    call_with_default_args(keywords)
