from RePoE.parser.util import write_json, call_with_default_args
from RePoE.parser import Parser_Module


class flavour(Parser_Module):
    def write(self) -> None:
        root = {}
        for flavour in self.relational_reader["FlavourText.dat64"]:
            if flavour["Id"] in root:
                print("Duplicate flavour id:", flavour["Id"])
            else:
                root[flavour["Id"]] = flavour["Text"]

        write_json(root, self.data_path, "flavour")


if __name__ == "__main__":
    call_with_default_args(flavour)
