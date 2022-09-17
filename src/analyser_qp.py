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
        question_list = self._generate(
            raw_ocr_data, longest_sequence, pdfname, page_cnt, *CONTENT_AREA_BOUND)
        return question_list

    def _generate(self, raw_ocr_data, question_number_sequence, pdfname, page_cnt,
                  left_bound, right_bound, top_bound, bottom_bound):
        question_list = []

        for idx, item in enumerate(question_number_sequence):

            # there's a gap, skip this question
            if idx != len(question_number_sequence) - 1 and \
                    int(question_number_sequence[idx + 1][11]) != int(item[11]) + 1:
                continue

            coords = []
            text = ""

            # for every page if not blank page, not non-exist page,
            # get all the way down to next question or end of page

            if idx == len(question_number_sequence) - 1:
                page_upper_bound = page_cnt
            else:
                page_upper_bound = question_number_sequence[idx + 1][1] + 1

            for page_idx in range(item[1], page_upper_bound):

                # page is blank
                if AnalyserModel._is_blank_page(AnalyserModel._ocr_data_on_page(raw_ocr_data, page_idx)):
                    break

                data_on_page = AnalyserModel._ocr_data_in_range(
                    AnalyserModel._ocr_data_on_page(raw_ocr_data, page_idx), left_bound, right_bound, top_bound, bottom_bound)

                # first question is on the page
                if page_idx == item[1]:
                    top_coord = item[7]
                else:
                    top_coord = top_bound

                # last question is on the page
                if idx != len(question_number_sequence) - 1 and \
                        page_idx == question_number_sequence[idx + 1][1]:
                    bottom_coord = question_number_sequence[idx + 1][7]
                else:
                    bottom_coord = AnalyserModel._last_character_bottom_coord(
                        data_on_page)

                # if the boxed area is empty
                if len(AnalyserModel._raw_ocr_data_filter
                       (AnalyserModel._ocr_data_in_range(
                        data_on_page, left_bound, right_bound, top_coord, bottom_coord
                       ))) == 0:
                    break

                coords.append({"page_num": page_idx, "left": left_bound, "right": right_bound,
                               "top": top_coord, "bottom": bottom_coord})

                text += AnalyserModel._merge_text(AnalyserModel._ocr_data_in_range(
                    data_on_page, left_bound, right_bound, top_coord, bottom_coord))

            question_list.append(AnalyserModel._make_question(pdfname, int(item[11]),
                                                              coords, text))
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

    debug(done_data, pdfname)

# debug is used for real debug lol


def debug(question_list, pdfname):

    pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
    images = convert_from_path(pdfpath)

    images = map(AnalyserModel._image_preprocessing, images)

    for idx, image in enumerate(images):

        new_image = image

        # # print line
        # new_image = cv2.line(
        #     new_image, (175, 0), (175, new_image.shape[0]), (0, 100, 0), 2)
        # new_image = cv2.line(new_image, (0, 2210),
        #                      (new_image.shape[1], 2210), (0, 100, 0), 2)
        # new_image = cv2.line(new_image, (0, 150),
        #                      (new_image.shape[1], 150), (0, 100, 0), 2)
        # new_image = cv2.line(new_image, (1550, 0),
        #                      (1550, new_image.shape[0]), (0, 100, 0), 2)

        DATA = []

        for item in DATA:
            if item[1] == idx:
                new_image = cv2.rectangle(
                    new_image, (item[6], item[7]), (item[6] + item[8], item[7] + item[9]), (0, 0, 0), 2)

        # print questions
        for item in question_list:
            for question in item["location"]:

                if question["page_num"] == idx:
                    new_image = cv2.rectangle(
                        new_image, (question["left"], question["top"]), (question["right"], question["bottom"]), (0, 0, 0), 2)
                    # new_image = cv2.putText(
                    #     new_image, item["text"], (question["left"], question["bottom"]),  cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

        # write to images
        cv2.imwrite(DEBUG_DIR_PATH + "images/image" +
                    str(idx) + ".png", new_image)

        # write question data
        with open(DEBUG_DIR_PATH + "json/analyser_result.json", "w") as debugfile:
            debugfile.write(json.dumps(question_list))


if __name__ == "__main__":
    exit(main())
