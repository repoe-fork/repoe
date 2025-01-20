from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_json


class audio(Parser_Module):
    def write(self) -> None:
        root = {}
        for audio in self.relational_reader["NPCTextAudio.dat64"]:
            root[audio["Id"]] = {
                "npcs": list(
                    map(
                        lambda npc: {"name": npc["Name"], "short_name": npc["ShortName"],
                                     "id": npc["Id"]},
                        audio["NPCs"],
                    )
                ),
                "characters": [c["Name"] for c in audio["Characters"]] or None,
                "text": audio["Text"],
                "audio": audio["AudioFiles"],
            }
        for event in self.relational_reader["CharacterEventTextAudio.dat64"]:
            audio = event["TextAudio"]
            root[audio["Id"]] = {
                "events": [event["Event"]],
                "characters": [event["Character"]["Name"]],
                "text": audio["Text"],
                "audio": [audio["SoundFile"]],
            }

        write_json(root, self.data_path, "audio")


if __name__ == "__main__":
    call_with_default_args(audio)
