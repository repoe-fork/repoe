from RePoE.parser.util import write_json, call_with_default_args
from RePoE.parser import Parser_Module


class lab_layout(Parser_Module):
    def write(self) -> None:
        layouts = self.relational_reader["LabyrinthSectionLayout.dat64"]
        layouts.build_index("LabyrinthSectionKey")
        result = {
            row["Id"]: {
                "group": row["ExclusionGroup"]["Id"] if row["ExclusionGroup"] else None,
                "difficulty": row["Unknown0"],
                "section": row["Unknown2"],
                "rooms": [
                    {
                        "row_id": room.rowid,
                        "x": room["Float0"],
                        "y": room["Float1"],
                        "connections": [conn.rowid for conn in room["LabyrinthSectionLayoutKeys"]],
                        "secret_1": room["LabyrinthSecretsKey0"]["Id"] if room["LabyrinthSecretsKey0"] else None,
                        "secret_2": room["LabyrinthSecretsKey1"]["Id"] if room["LabyrinthSecretsKey1"] else None,
                        "override": next(
                            iter(override["Id1"] for override in room["LabyrinthNodeOverridesKeys"]), None
                        ),
                        "areas": self.areas(room["LabyrinthAreasKey"], row["Unknown0"]),
                    }
                    for room in layouts.index["LabyrinthSectionKey"][row]
                ],
            }
            for row in self.relational_reader["LabyrinthSection.dat64"]
        }

        write_json(result, self.data_path, "lab_layout")

    def areas(self, areas, difficulty):
        if not areas:
            return None
        match difficulty:
            case 1:
                return [area["Id"] for area in areas["Normal_WorldAreasKeys"]]
            case 2:
                return [area["Id"] for area in areas["Cruel_WorldAreasKeys"]]
            case 3:
                return [area["Id"] for area in areas["Merciless_WorldAreasKeys"]]
            case 4:
                return [area["Id"] for area in areas["Endgame_WorldAreasKeys"]]


if __name__ == "__main__":
    call_with_default_args(lab_layout)
