from RePoE.parser.util import write_json, call_with_default_args
from RePoE.parser import Parser_Module


class cost_types(Parser_Module):
    def write(self) -> None:
        root = {}
        for row in self.relational_reader["CostTypes.dat64"]:
            root[row["Id"]] = {
                "stat": row["StatsKey"]["Id"] if row["StatsKey"] else None,
                "format_text": row["FormatText"],
            }
        write_json(root, self.data_path, "cost_types")


if __name__ == "__main__":
    call_with_default_args(cost_types)
