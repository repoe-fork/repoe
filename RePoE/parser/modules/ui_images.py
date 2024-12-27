from typing import Iterator
from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, export_image, crop
from PyPoE.poe.file.idl import IDLFile, IDLRecord

IMAGES_TO_EXPORT = set("Art/2DArt/UIImages/InGame/" + image for image in ["Buff", "Debuff", "Flask", "Charges"])


class ui_images(Parser_Module):
    def write(self) -> None:
        idl = IDLFile()
        idl.read(file_path_or_raw=self.file_system.get_file("Art/UIImages1.txt"))
        self.export(idl)

    def export(self, idl: Iterator[IDLRecord]):
        for record in idl:
            if record.destination in IMAGES_TO_EXPORT:
                export_image(
                    record.source,
                    self.data_path,
                    self.file_system,
                    record.destination,
                    compose=crop(record.x1, record.y1, record.x2 + 1, record.y2 + 1),
                )


if __name__ == "__main__":
    call_with_default_args(ui_images)
