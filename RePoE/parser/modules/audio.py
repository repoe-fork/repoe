import os
from textwrap import shorten
from typing import Any


from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args


class audio(Parser_Module):
    def write(self) -> None:
        npcs = self.relational_reader["NPCs.dat64"]
        for audio in self.relational_reader["NPCTextAudio.dat64"]:
            if not audio["Mono_AudioFile"]:
                continue

            npc = npcs[min(audio["Keys0"])]
            dir = os.path.join("data", "Audio", npc["ShortName"] if npc["ShortName"] else npc["Name"])
            os.makedirs(dir, exist_ok=True)
            basename = os.path.join(dir, shorten(audio["Text"], 80) if audio["Text"] else audio["Id"])

            with open(basename + os.path.splitext(audio["Mono_AudioFile"])[1], "wb") as file:
                file.write(self.file_system.get_file(audio["Mono_AudioFile"]))
            if audio["Text"]:
                with open(basename + ".txt", "w") as file:
                    file.write(audio["Text"])


if __name__ == "__main__":
    call_with_default_args(audio)
