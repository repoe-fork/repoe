from RePoE.parser.util import write_json, call_with_default_args
from RePoE.parser import Parser_Module


class mod_types(Parser_Module):
    def write(self) -> None:
        mod_types = {
            row["Name"]: {
                "sell_price_types": [key["Id"] for key in row["ModSellPriceTypesKeys"]],
            }
            for row in self.relational_reader["ModType.dat64"]
        }

        write_json(mod_types, self.data_path, "mod_types")


if __name__ == "__main__":
    call_with_default_args(mod_types)
