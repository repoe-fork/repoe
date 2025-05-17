from RePoE.parser.util import call_with_default_args, write_any_json
from RePoE.parser import Parser_Module


class item_inherent_skills(Parser_Module):
    def write(self) -> None:
        item_inherent_skills = {
            row["BaseItemType"]["Id"]: {
                "base_item_type": row["BaseItemType"]["Id"],
                "skills_granted": [
                    skill["BaseItemType"]["Id"]
                    for skill in row["SkillsGranted"]
                ] if row["SkillsGranted"] else []
            }
            for row in self.relational_reader["ItemInherentSkills.dat64"]
        }

        write_any_json(item_inherent_skills, self.data_path, "item_inherent_skills")


if __name__ == "__main__":
    call_with_default_args(item_inherent_skills)
