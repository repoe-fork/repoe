from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_json


class audio(Parser_Module):
    def write(self) -> None:
        root = {}
        for audio in self.relational_reader["NPCTextAudio.dat64"]:
            root[audio["Id"]] = {
                "npcs": list(
                    map(
                        lambda npc: {"name": npc["Name"], "short_name": npc["ShortName"], "id": npc["Id"]},
                        audio["NPCs"],
                    )
                ),
                "text": audio["Text"],
                "mono": audio["Mono_AudioFile"],
                "stereo": audio["Stereo_AudioFile"],
                "video": audio["Video"],
            }

        write_json(root, self.data_path, "audio")


if __name__ == "__main__":
    call_with_default_args(audio)
