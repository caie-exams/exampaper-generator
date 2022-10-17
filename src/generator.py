
import re
import random
import string
from pdfrw import PdfReader, PdfWriter, PageMerge, PdfDict
from reportlab.pdfgen import canvas
from io import BytesIO
from configuration import *

from model.analyser_model import AnalyserModel


class Generator:

    def __init__(self, background_filepath):
        self.background_filepath = background_filepath
        # constants
        self.PAGE_PADDING_PERCENT = 0.05
        self.TEXT_HEIGHT = 10

    def process(self, question_list: list, output_filepath: str, display_qp_origin: bool):
        """
        input a list of questions, and output a pdf document
        """

        # gather background information
        background_template_file = PdfReader(self.background_filepath)
        background_template_page = background_template_file.pages[0]
        bwidth, bheight = Generator.get_pdf_shape(background_template_page)

        embed_data_cache = []

        # get data
        for question in question_list:

            for idx, location in enumerate(question["location"]):

                # get embed object
                embed_filename = location["hashed_filename"]
                embed_file = PdfReader(
                    DATA_DIR_PATH + "cached_pdf/" + embed_filename + ".pdf")
                embed_page = embed_file.pages[0]

                embed_object = PageMerge().add(embed_page)[0]

                # scale the embed object
                ewidth, eheight = Generator.get_pdf_shape(embed_page)
                if display_qp_origin and idx == 0:
                    k = Generator.calculate_resize_factor(
                        bwidth * (1-2*self.PAGE_PADDING_PERCENT), bheight * (1-2*self.PAGE_PADDING_PERCENT), ewidth, eheight + 2 * self.TEXT_HEIGHT)
                else:
                    k = Generator.calculate_resize_factor(
                        bwidth * (1-2*self.PAGE_PADDING_PERCENT), bheight * (1-2*self.PAGE_PADDING_PERCENT), ewidth, eheight)
                embed_object.scale(k)
                ewidth *= k
                eheight *= k

                # save the info to cache
                embed_data_cache.append(
                    {"pdf": location["hashed_filename"],
                        "obj": embed_object, "w": ewidth, "h": eheight, "loc": location, "idx": idx})

        # arrange the layout

        text_data_cache = []
        embed_data_cache_tmp = []

        page_cnt = 0
        question_cnt = 0
        fufilled_height = bheight * self.PAGE_PADDING_PERCENT

        while len(embed_data_cache) > 0:

            embed_data = embed_data_cache[0]

            text = "_".join(embed_data["pdf"].split(
                "_")[:4]) + " Q" + embed_data["pdf"].split("_")[4]

            if display_qp_origin:
                text = str(question_cnt + 1) + "." + "     " + text
            else:
                text = str(question_cnt + 1) + "."

            text_data = {"t": text, "x": bwidth *
                         self.PAGE_PADDING_PERCENT, "y": bheight - fufilled_height, "page": page_cnt}

            fufilled_height += embed_data["h"]

            if fufilled_height >= bheight * (1 - self.PAGE_PADDING_PERCENT):
                fufilled_height = bheight * self.PAGE_PADDING_PERCENT
                page_cnt += 1
                continue

            if embed_data["idx"] == 0:
                question_cnt += 1

            embed_data_cache.pop(0)

            embed_data["page"] = page_cnt
            embed_data["x"], embed_data["y"] = Generator.get_origin_coords(
                embed_data["loc"], embed_data["w"], embed_data["h"])

            print(embed_data["x"])

            embed_data["x"] += bwidth * self.PAGE_PADDING_PERCENT
            embed_data["y"] += bheight - fufilled_height

            if display_qp_origin and embed_data["idx"] == 0:
                embed_data["y"] -= 2 * self.TEXT_HEIGHT

            if embed_data["idx"] == 0:
                text_data_cache.append(text_data)
            embed_data_cache_tmp.append(embed_data)

        embed_data_cache = embed_data_cache_tmp

        # embed pdf into the page
        page_list = [PdfReader(self.background_filepath).pages[0]
                     for i in range(0, embed_data_cache[-1]["page"] + 1)]

        while len(embed_data_cache) > 0:
            embed_data = embed_data_cache.pop(0)
            Generator.embed_pdf(
                page_list[embed_data["page"]], embed_data["obj"], embed_data["x"], embed_data["y"])

        # add page number and question text
        for idx, page in enumerate(page_list):
            Generator.put_text_on_pdf(
                page, "# " + str(idx + 1), bwidth * (1-self.PAGE_PADDING_PERCENT) - 5, 10)

        for text_data in text_data_cache:
            pg, t, x, y = page_list[text_data["page"]
                                    ], text_data["t"], text_data["x"], text_data["y"]

            if not display_qp_origin:
                x = 10
                y -= 8

            Generator.put_text_on_pdf(pg, t, x, y,
                                      lambda c: c.rect(x-2, y-2, len(t) * 6, self.TEXT_HEIGHT + 2, fill=False))

        # write the pdf
        Generator.merge_pages_and_write_pdf(output_filepath, page_list)

    @ staticmethod
    def put_text_on_pdf(page, text, x, y, styling=None):
        packet = BytesIO()
        c = canvas.Canvas(packet)

        if styling is not None:
            styling(c)

        c.drawString(x, y, text)
        c.showPage()
        c.save()
        packet.seek(0)
        text_overlay = PdfReader(packet).pages[0]
        Generator.embed_pdf(page, text_overlay, 0, 0)
        packet.close()

    @ staticmethod
    def generate_random_str(length: int):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    @staticmethod
    def get_origin_coords(location, ewidth, eheight):
        """
        the embed pdf is actually just a mediabox of a larger origin pdf page,
        the coordinates in background is the bottom left corner of the origin pdf page
        this function get x, y coordinate from a bunch of parameters

        if shift is zero, the bottom left of origin pdf is default placed on 0,0
        """

        left, right, top, bottom = location["left"], location["right"], location["top"], location["bottom"]

        origin_width, origin_height = ewidth / \
            (right - left), eheight / (bottom - top)

        x = - origin_width * left
        y = - origin_height * (1 - bottom)

        return x, y

    @ staticmethod
    def get_pdf_shape(pdfpage: PdfDict):
        """
        input pdf page, return width and height
        """

        x, y, x1, y1 = tuple(float(x) for x in pdfpage.MediaBox)

        width, height = abs(x1 - x), abs(y1 - y)

        if pdfpage.Rotate is not None and \
                int(pdfpage.Rotate) in [90, 270]:

            width, height = height, width

        return width, height

    @ staticmethod
    def calculate_resize_factor(bwidth, bheight, ewidth, eheight):
        k = 1
        if ewidth > bwidth or eheight > bheight:
            k = min(bwidth / ewidth, bheight / eheight)
        return k

    @ staticmethod
    def embed_pdf(background_page, embed_object,  x, y):

        embed_object.x = x
        embed_object.y = y

        PageMerge(background_page).add(embed_object, prepend=False).render()

    @ staticmethod
    def merge_pages_and_write_pdf(output_filepath, page_list):
        output = PdfWriter()

        for page in page_list:
            output.addpage(page)

        output.write(output_filepath)


def main():

    # qp_list = [
    #     {
    #         "pdfname": "9231_s17_qp_12",
    #         "question_num": 4,
    #         "location": [
    #             {
    #                 "page_num": 5,
    #                 "left": 0.07562008469449485,
    #                 "right": 0.940713853599516,
    #                 "top": 0.07391149819483772,
    #                 "bottom": 0.9055081499424545,
    #                 "hashed_filename": "9231_s17_qp_12_4_5"
    #             }
    #         ],
    #         "text": "4\n\n(i) Find the value of k for which the set of linear equations\n\nhas no unique solution.\n\nx + 3y + kz = 4,\n4x \u2212 2y \u2212 10z = \u22125,\nx + y + 2z = 1,\n\n[3]\n\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n\n\f(ii) For this value of k, find the set of possible solutions, giving your answer in the form\n` a\nx\ny = a + tb,\nz\nwhere a and b are vectors and t is a scalar.\n\n[3]\n\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n........................................................................................................................................................\n\n\f"
    #     }
    # ]

    qp_list = AnalyserModel.load_debugfile("categoriser_qp")
    ms_list = AnalyserModel.load_debugfile("categoriser_ms")

    generator = Generator("template/alpha_testing.pdf")

    generator.process(qp_list, DEBUG_DIR_PATH + "pdf/qp.pdf", True)
    generator.process(ms_list, DEBUG_DIR_PATH + "pdf/ms.pdf", False)


if __name__ == "__main__":
    exit(main())
