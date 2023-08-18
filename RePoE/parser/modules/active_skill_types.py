from RePoE.parser.util import call_with_default_args, write_json
from RePoE.parser import Parser_Module


class active_skill_types(Parser_Module):
    def write(self) -> None:
        types = [row["Id"] for row in self.relational_reader["ActiveSkillType.dat64"]]
        write_json(types, self.data_path, "active_skill_types")


if __name__ == "__main__":
    call_with_default_args(active_skill_types)
