from model.analyser_model import *

from pdf2image import convert_from_path
from longest_increasing_subsequence import longest_increasing_subsequence
import re


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

    def process(self, pdfname, tesseract_config=None):

        # load config
        config = AnalyserModel._load_config(pdfname.split("_")[0])[
            "analyser"]

        # load page bound

        CONTENT_AREA_BOUND = []
        for pdfname_regex in config["page_bound"]:
            if re.match(pdfname_regex, pdfname) is not None:
                CONTENT_AREA_BOUND = config["page_bound"][pdfname_regex]
                break
        if CONTENT_AREA_BOUND == []:
            raise Exception("page bound not specified in config")

        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        images = convert_from_path(pdfpath)
        images = list(map(AnalyserModel._image_preprocessing, images))
        image_width, image_height = images[0].shape[1], images[0].shape[0]

        page_cnt = len(images)

        # raw_ocr_data = AnalyserModel._scan_to_get_raw_ocr_data(
        #     images, tesseract_config)

        raw_ocr_data = []
        for idx in range(0, page_cnt):
            raw_ocr_data += AnalyserModel._pdfplumber_get_raw_data(
                pdfpath, idx, images[idx])

        # eliminate unwanted content for each page
        unwanted_content_list = []
        for pdfname_regex in config["unwanted_content"]:
            if re.match(pdfname_regex, pdfname) is not None:
                unwanted_content_list += config["unwanted_content"][pdfname_regex]
        raw_ocr_data = AnalyserModel._add_break_point(
            raw_ocr_data, unwanted_content_list, 0, page_cnt - 1, *CONTENT_AREA_BOUND)

        AnalyserModel.write_debugfile("raw_ocr_data", raw_ocr_data)

        # find questiom num data
        question_num_data = AnalyserModel._locate_question_numbers(
            raw_ocr_data, 1, page_cnt - 1, *CONTENT_AREA_BOUND)

        longest_sequence = longest_increasing_subsequence(
            question_num_data, False, lambda x: int(x[11]))
        # question_list = self._generate_mcq(
        #     raw_ocr_data, longest_sequence,  pdfname)
        question_list = AnalyserModel._generate_questions(
            raw_ocr_data, longest_sequence, pdfname, page_cnt, image_width, image_height, * CONTENT_AREA_BOUND)

        return question_list


# main is used for debug
def main():

    pdfname = "9608_w20_qp_12"
    # 34

    analyser = AnalyserFixedQN()
    # print("first scan!")
    # done_data1 = analyser.process(pdfname, "-l arial --psm 3")
    print("second scan!")
    done_data2 = analyser.process(pdfname, "-l arial --psm 12")

    # done_data = done_data2
    # for data1 in done_data1:
    #     found = False
    #     for data2 in done_data2:
    #         if data2["question_num"] == data1["question_num"]:
    #             found = True
    #             break

    #     if not found:
    #         done_data.append(data1)

    # done_data.sort(key=lambda x: x["question_num"])

    print("start deugging")

    AnalyserModel.debug(done_data2, pdfname)


if __name__ == "__main__":
    exit(main())
