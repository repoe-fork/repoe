from RePoE.parser.util import call_with_default_args, export_image, write_json
from RePoE.parser import Parser_Module


class characters(Parser_Module):
    def write(self):
        root = []
        should_export_images = self.language == "English"
        for row in self.relational_reader["Characters.dat64"]:
            character = {
                "metadata_id": row["Id"],
                "integer_id": row["IntegerId"],
                "name": row["Name"],
                "description": row["Description"],
                "base_stats": {
                    "life": row["BaseMaxLife"],
                    "mana": row["BaseMaxMana"],
                    "strength": row["BaseStrength"],
                    "dexterity": row["BaseDexterity"],
                    "intelligence": row["BaseIntelligence"],
                    "unarmed": {
                        "attack_time": row["WeaponSpeed"],
                        "min_physical_damage": row["MinDamage"],
                        "max_physical_damage": row["MaxDamage"],
                        "range": row["MaxAttackDistance"],
                    },
                },
            }
            if row["PassiveTreeImage"]:
                character["passive_tree_image"] = row["PassiveTreeImage"]
                if should_export_images:
                    export_image(row["PassiveTreeImage"], self.data_path, self.file_system)
            root.append(character)
        write_json(root, self.data_path, "characters")


if __name__ == "__main__":
    call_with_default_args(characters)
