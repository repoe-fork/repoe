from RePoE.parser import Parser_Module
from RePoE.parser.util import write_json, call_with_default_args


class default_monster_stats(Parser_Module):
    def write(self) -> None:
        root = {}
        for row in self.relational_reader["DefaultMonsterStats.dat64"]:
            root[row["DisplayLevel"]] = {
                "physical_damage": row["Damage"],
                "evasion": row["Evasion"],
                "accuracy": row["Accuracy"],
                "life": row["Life"],
                "experience": row["Experience"],
                "ally_life": row["AllyLife"],
                "armour": row["Armour"],
            }
        write_json(root, self.data_path, "default_monster_stats")


if __name__ == "__main__":
    call_with_default_args(default_monster_stats)
