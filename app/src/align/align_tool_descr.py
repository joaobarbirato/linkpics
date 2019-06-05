"""
    Align tool for image descriptions
    @author: João Gabriel Melo Barbirato
"""

from app.src.align.idgen import Generator
from app.align_module import models

_COLOR_TEXT_OPEN = "<b>"
_COLOR_TEXT_CLOSE = "</b>"


class AlignToolDescr:
    def __init__(self, title=None, sub=None, text=None, method=None, align_group=None):
        self.title = title
        self.sub = sub
        self.text = text
        self.method = method
        self.group = align_group

        image_desc_gen = Generator(
            title=self.title, sub=self.sub, text=self.text,
            aligned_subs=self.group.get_all_alignments()
        )
        image_desc_gen.generate_descriptions(type="N-MATCH")
        self.descr = image_desc_gen.get_gen_descr()

    def get_descr(self):
        return self.descr

    def color_text(self):
        for snt in self.descr:
            if snt in self.text or snt in self.sub or snt in self.title:
                self.text = self.text.replace(snt, _COLOR_TEXT_OPEN + snt + _COLOR_TEXT_CLOSE)
                self.sub = self.sub.replace(snt, _COLOR_TEXT_OPEN + snt + _COLOR_TEXT_CLOSE)
                self.title = self.title.replace(snt, _COLOR_TEXT_OPEN + snt + _COLOR_TEXT_CLOSE)

        return [self.title, self.sub, self.text]
