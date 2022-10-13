import math
from generator import Generator
from pdfrw import PdfReader
from model.analyser_model import AnalyserModel
from configuration import *


class GeneratorMSMCQ(Generator):

    def __init__(self, background_filepath):
        self.background_filepath = background_filepath
        # constants
        self.PAGE_PADDING_PERCENT = 0.1
        self.QUESTION_ON_PAGE = 30
        self.X_SHIFT_1 = 30
        self.X_SHIFT_2 = 280

    def process(self, msmcq_list: list, output_filepath: str):
        """
        input a list of questions, and output a pdf document
        """

        background_template_file = PdfReader(self.background_filepath)
        background_template_page = background_template_file.pages[0]
        bwidth, bheight = Generator.get_pdf_shape(background_template_page)

        # arrange the layout
        page_cnt = math.ceil(len(msmcq_list) / self.QUESTION_ON_PAGE)
        page_list = [PdfReader(self.background_filepath).pages[0]
                     for i in range(0, page_cnt)]

        # add page number
        for idx, page in enumerate(page_list):
            Generator.put_text_on_pdf(
                page, "# " + str(idx + 1), bwidth * (1-self.PAGE_PADDING_PERCENT) - 5, 10)

        # add question text
        for idx, page in enumerate(page_list):
            for mcq_idx in range(30 * idx, min(30 * (idx+1), len(msmcq_list))):

                text = msmcq_list[mcq_idx]["text"]

                y_shift = bheight * \
                    (1-2*self.PAGE_PADDING_PERCENT) / \
                    self.QUESTION_ON_PAGE * (mcq_idx - 30 * idx)

                y_coord = bheight - \
                    (bheight * self.PAGE_PADDING_PERCENT + y_shift) - 5

                x1 = bwidth * self.PAGE_PADDING_PERCENT + \
                    self.X_SHIFT_1 - len(str(mcq_idx + 1)) * 3 + 1
                x2 = bwidth * self.PAGE_PADDING_PERCENT + self.X_SHIFT_2

                Generator.put_text_on_pdf(page, str(mcq_idx + 1), x1, y_coord)
                Generator.put_text_on_pdf(page, text, x2, y_coord)

        # write the pdf
        Generator.merge_pages_and_write_pdf(output_filepath, page_list)


def main():

    all_question_list = AnalyserModel.load_debugfile("controller_results")

    ms_list = [
        question for question in all_question_list if "ms" in question["pdfname"] and question["pdfname"].split("_")[-1][0] == "1"]

    # generate question

    generator = GeneratorMSMCQ("template/ms_mcq.pdf")
    generator.process(ms_list[:40], DEBUG_DIR_PATH + "pdf/ms_mcq.pdf")


if __name__ == "__main__":
    exit(main())
