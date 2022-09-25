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

    def process(self, pdfname, tesseract_config="--oem 0"):

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
            images, tesseract_config)

        # eliminate unwanted content for each page
        unwanted_content_list = []
        for pdfname_regex in config["unwanted_content"]:
            if re.match(pdfname_regex, pdfname) is not None:
                unwanted_content_list += config["unwanted_content"][pdfname_regex]
        raw_ocr_data = AnalyserModel._add_break_point(
            raw_ocr_data, unwanted_content_list, 0, page_cnt - 1, *CONTENT_AREA_BOUND)

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

    pdfname = "9701_w18_qp_22"
    # 34

    # analyser = AnalyserFixedQN()
    # print("first scan!")
    # done_data1 = analyser.process(pdfname, "-l arial --psm 3")
    # print("second scan!")
    # done_data2 = analyser.process(pdfname, "-l arial --psm 11")

    # AnalyserModel.write_debugfile("done_data1", done_data1)
    # AnalyserModel.write_debugfile("done_data2", done_data2)

    done_data1 = AnalyserModel.load_debugfile("done_data1")
    done_data2 = AnalyserModel.load_debugfile("done_data2")

    combined_data = sorted(done_data1 + done_data2,
                           key=lambda x: x["question_num"] * 100 + len(x["location"]))

    done_data = []

    i = 0
    while i < len(combined_data):
        all_same_question_list = []
        j = i
        while j < len(combined_data):
            if combined_data[j]["question_num"] == combined_data[i]["question_num"]:
                all_same_question_list.append(combined_data[j])
                j = j + 1
            else:
                break

        location_list = []
        [location_list.extend(question["location"])
         for question in all_same_question_list]

        sorted_location_list = sorted(
            location_list, key=lambda x: x["page_num"] * 1e8 - (x["bottom"] - x["top"]) * 100)

        print(all_same_question_list)
        print(sorted_location_list)
        print("===============")

        data = combined_data[i]
        data["location"] = [sorted_location_list[k] for k in range(0, len(sorted_location_list))
                            if k == 0 or sorted_location_list[k]["page_num"] != sorted_location_list[k-1]["page_num"]]

        done_data.append(data)

        i = j

    print("start deugging")

    AnalyserModel.debug(done_data, pdfname)


if __name__ == "__main__":
    exit(main())
