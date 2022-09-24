from model.analyser_model import *

import cv2
import pytesseract
from pdf2image import convert_from_path
from longest_increasing_subsequence import longest_increasing_subsequence
import time


class AnalyserFixedQN(AnalyserModel):
    """
    use to process most questions paper and some mcqs that
    - does not have a grid line
    - the position of quesition numbers are fixed 

    takes name of pdf and spit out questions raw data

    input - name of pdf
    output - individual quesitons

    relation is one-to-many
    """

    def process(self, pdfname):

        # load config
        config = AnalyserModel._load_config(pdfname.split("_")[0])[
            "analyser"]

        CONTENT_AREA_BOUND = [175, 1550, 150, 2210]

        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        images = convert_from_path(pdfpath)
        images = list(map(AnalyserModel._image_preprocessing, images))
        image_width, image_height = images[0].shape[1], images[0].shape[0]

        page_cnt = len(images)

        raw_ocr_data = AnalyserModel._scan_to_get_raw_ocr_data(
            images, "-l arial")

        AnalyserModel.write_debugfile("raw_ocr_data", raw_ocr_data)

        # eliminate unwanted content for each page
        unwanted_content_list = []
        for pdfname_regex in config["unwanted_content"]:
            if re.match(pdfname_regex, pdfname) is not None:
                unwanted_content_list += config["unwanted_content"][pdfname_regex]
        raw_ocr_data = AnalyserModel._add_break_point(
            raw_ocr_data, unwanted_content_list, start_idx=0, end_idx=page_cnt - 1)

        AnalyserModel.write_debugfile("raw_ocr_data_", raw_ocr_data)
        # find questiom num data

        question_num_data = AnalyserModel._locate_question_numbers(
            raw_ocr_data, 0, page_cnt - 1, *CONTENT_AREA_BOUND)

        longest_sequence = longest_increasing_subsequence(
            question_num_data, False, lambda x: int(x[11]))
        # question_list = self._generate_mcq(
        #     raw_ocr_data, longest_sequence,  pdfname)
        question_list = AnalyserModel._generate_questions(
            raw_ocr_data, longest_sequence, pdfname, page_cnt, image_width, image_height, * CONTENT_AREA_BOUND)

        AnalyserModel.write_debugfile("question_list", question_list)
        return question_list


# main is used for debug
def main():

    pdfname = "9701_w18_qp_13"

    analyser = AnalyserFixedQN()
    done_data = analyser.process(pdfname)

    # print(done_data)

    print("start deugging")

    AnalyserModel.debug(done_data, pdfname)


if __name__ == "__main__":
    exit(main())
