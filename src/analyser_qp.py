from model.analyser_model import *
from model.processor_model import *

import cv2
import pytesseract
from pdf2image import convert_from_path
from longest_increasing_subsequence import longest_increasing_subsequence
import time


class AnalyserQP(AnalyserModel, ProcessorModel):
    """
    takes name of pdf and spit out questions raw data

    input - name of pdf
    output - individual quesitons

    relation is one-to-many
    """

    def _process(self, pdfname):

        self.config = CONFIG.get_config(pdfname)

        CONTENT_AREA_BOUND = [175, 1550, 150, 2210]

        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        images = convert_from_path(pdfpath)
        images = list(map(AnalyserModel._image_preprocessing, images))
        page_cnt = len(images)

        raw_ocr_data = AnalyserModel._scan_to_get_raw_ocr_data(
            images)
        # raw_ocr_data = self.raw_ocr_data_filter(raw_ocr_data)

        # debug
        with open(DEBUG_DIR_PATH + "json/raw_ocr_data.json", "w") as debugfile:
            debugfile.write(json.dumps(raw_ocr_data))

        question_num_data = AnalyserModel._locate_question_numbers(
            raw_ocr_data, 0, page_cnt, *CONTENT_AREA_BOUND)

        longest_sequence = longest_increasing_subsequence(
            question_num_data, False, lambda x: int(x[11]))
        # question_list = self._generate_mcq(
        #     raw_ocr_data, longest_sequence,  pdfname)
        question_list = self._generate_questions(
            raw_ocr_data, longest_sequence, pdfname, page_cnt, *CONTENT_AREA_BOUND)
        return question_list


# main is used for debug
def main():

    done_data = []
    pdfname = "0620_s20_qp_11"

    analyser = AnalyserQP(done_data)
    analyser.start()
    analyser.add_task(pdfname)
    isrunning = True
    analyser.stop()
    while isrunning:
        isalive, isrunning, leng = analyser.status()
        print(isalive, isrunning, leng)
        time.sleep(1)

    print(done_data)

    print("start deugging")

    AnalyserModel.debug(done_data, pdfname)


if __name__ == "__main__":
    exit(main())
