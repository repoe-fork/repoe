from RePoE.parser.util import call_with_default_args, write_json
from RePoE.parser import Parser_Module

influences = ["shaper", "elder", "crusader", "eyrie", "basilisk", "adjudicator"]


class item_classes(Parser_Module):
    def write(self) -> None:
        item_classes = {
            row["Id"]: {
                "name": row["Name"],
                "category_id": row["ItemClassCategory"]["Id"] if row["ItemClassCategory"] else None,
                "category": row["ItemClassCategory"]["Text"] if row["ItemClassCategory"] else None,
            }
            for row in self.relational_reader["ItemClasses.dat64"]
        }

        write_json(item_classes, self.data_path, "item_classes")


if __name__ == "__main__":
    call_with_default_args(item_classes)
