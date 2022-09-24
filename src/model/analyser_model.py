from configuration import *

import cv2
import pytesseract
import numpy as np
import re
from math import ceil, floor
from pdf2image import convert_from_path
from fuzzysearch import find_near_matches
from func_timeout import func_timeout, FunctionTimedOut


class AnalyserModel:

    BREAK_POINT_TEXT = "@@BREAKPOINT@@"

    """
    stores staticmethods that are commonly used by analysers

    this class is default for analysing quesiton papers, can be inherited
    """

    @staticmethod
    def _load_config(config_name: str) -> list:
        """
        input config name (without json) and return the config
        """
        config_path = CONFIG_DIR_PATH + config_name + ".json"
        with open(config_path, "r") as config_file:
            return json.loads(config_file.read())

    @ staticmethod
    def _scan_to_get_raw_ocr_data(images, tesseract_config=None):
        """
        taking pdf path
        returns a raw ocr data and the page count

        raw ocr data format

        | num     | data        |
        | ------- | ------      |
        | 0       | level       |
        | 1       | page_num    |
        | 2       | block_num   |
        | 3       | par_num     |
        | 4       | line_num    |
        | 5       | word_num    |
        | 6       | left        |
        | 7       | top         |
        | 8       | width       |
        | 9       | height      |
        | 10      | conf        |
        | 11      | text        |
        """

        # AnalyserModel.__find_ms_boundaries(images)

        raw_ocr_data = []
        for idx, image in enumerate(images):
            if tesseract_config is not None:
                raw_data = pytesseract.image_to_data(
                    image, config=tesseract_config)
            else:
                raw_data = pytesseract.image_to_data(
                    image)
            for item in raw_data.splitlines()[1:]:
                item_data = item.split('\t')
                item_data[:10] = map(int, item_data[:10])
                item_data[10] = float(item_data[10])
                item_data[1] = idx
                raw_ocr_data.append(item_data)

        return AnalyserModel._raw_ocr_data_filter(raw_ocr_data)

    @staticmethod
    def _locate_question_numbers(raw_ocr_data, start_page, end_page, left_bound, right_bound, top_bound, bottom_bound):
        """
        input raw_ocr_data and page range and coords of content area
        return list of ocr raw data of question numbers
        """

        # find the longest sequence of questions
        question_numbers = []

        for page_idx in range(start_page, end_page + 1):

            page = AnalyserModel._raw_ocr_data_filter(
                AnalyserModel._ocr_data_on_page(raw_ocr_data, page_idx))
            num_area = AnalyserModel._ocr_data_in_range(
                page, 0, left_bound, top_bound, bottom_bound)

            for match in num_area:
                match[11] = "".join(filter(str.isdigit, match[11]))
                if match[11] != "" and int(match[11]) > 0:
                    question_numbers.append(match)

        return question_numbers

    @ staticmethod
    def _image_preprocessing(img):
        """
        preprocess the image to apply change (like) greyscale
        """
        # gray scale
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        # thresholding
        # img = cv2.threshold(
        #     img, 128, 255, cv2.THRESH_BINARY_INV)[1]
        return img

    @ staticmethod
    def _raw_ocr_data_filter(raw_ocr_data):
        """
        filter out any non-text data
        """

        filtered_ocr_data = []
        for ocr_data in raw_ocr_data:
            if ocr_data[11] != "" and ocr_data[10] != -1.0:
                filtered_ocr_data.append(ocr_data)
        return filtered_ocr_data

    @ staticmethod
    def _ocr_data_in_range(raw_ocr_data, left, right, top,  bottom):
        """
        take in raw ocr data and coords of box
        return raw ocr data in the box
        """

        return [item for item in raw_ocr_data
                if (left == -1 or item[6] >= left)
                and (right == -1 or (item[6] + item[8]) <= right)
                and (top == -1 or item[7] >= top)
                and (bottom == -1 or (item[7] + item[9]) <= bottom)]

    @ staticmethod
    def _ocr_data_on_page(raw_ocr_data, pagenum):
        """
        taking raw ocr data
        returns ocr data on specific pdf page
        """

        return [item for item in raw_ocr_data if item[1] == pagenum]

    @ staticmethod
    def _merge_text(raw_ocr_data):
        """
        input raw_ocr_data
        return merged text in raw ocr data
        """

        return " ".join([word[11] for word in raw_ocr_data])

    @ staticmethod
    def _last_character_bottom_coord(raw_ocr_data):
        """
        input raw ocr data
        return last character on ocr data's bottom coord

        used to find the last quesiton on page
        """
        ans = -1
        for item in raw_ocr_data:
            ans = max(ans, item[7] + item[9])
        return ans

    @ staticmethod
    def _is_blank_page(raw_ocr_data):
        """
        test if BLANK PAGE is present on the page
        """

        for item in raw_ocr_data:
            if "BLANK" in item or "PAGE" in item:
                return True
        return False

    @ staticmethod
    def _make_question(pdfname,  question_number,  location, text=None):
        """
        \b
        question format:
        pdfname              string            name of pdf
        question_num         int               number of question
        location             list[dict]
            page_num         int               number of page
            left             float               percentage
            right            float               percentage
            top              float               percentage
            bottom           float               percentage
            hashed_filename  str               hashed filename of cropped images/pdfs
        text                 str               answer of mcq or text of question

        this is both suitable for question data and answer datas
        """

        return {"pdfname": pdfname,
                "question_num": question_number, "location": location, "text": text}

    @ staticmethod
    def _clean_text(text: str) -> str:
        # replace newline and tab with space
        text = text.replace("\n", " ")
        text = text.replace("\t", " ")
        # remove multiple spaces
        text = " ".join(text.split())
        # strip leading spaces
        text = text.strip()

        return text

    @staticmethod
    def _ocr_data_matches_string(raw_ocr_data: list, target_str: str) -> list:
        """
        takes ocr data, return the portion that fuzzy matches a string
        """

        # merge ocr data to text, and map the relation ship

        ocr_data_merged = ""
        ocr_data_text_map = {}

        for idx, data in enumerate(raw_ocr_data):
            start_idx = len(ocr_data_merged)
            ocr_data_merged += data[11] + " "
            end_idx = len(ocr_data_merged)

            for i in range(start_idx, end_idx):
                ocr_data_text_map[i] = idx

        try:
            matchs = func_timeout(1, find_near_matches,
                                  args=(target_str, ocr_data_merged), kwargs={"max_l_dist": int(len(target_str) * 0.2)})
        except FunctionTimedOut:
            return []

        if len(matchs) == 0:
            return []

        matched_ocr_data = []
        for match in matchs:
            prev_ocr_idx = -1
            for idx in range(match.start, match.end):
                ocr_idx = ocr_data_text_map[idx]
                if ocr_idx != prev_ocr_idx:
                    matched_ocr_data.append(raw_ocr_data[ocr_idx])
                prev_ocr_idx = ocr_idx

        # print(matched_ocr_data)
        return matched_ocr_data

    @staticmethod
    def _add_break_point(raw_ocr_data, unwanted_content_list, start_idx, end_idx):
        """
        input raw ocr data and function specific config
        """

        for page_idx in range(start_idx, end_idx + 1):
            ocr_data_in_range_on_page = AnalyserModel._ocr_data_on_page(
                raw_ocr_data, page_idx)
            for unwanted_content in unwanted_content_list:
                matched_ocr_data = AnalyserModel._ocr_data_matches_string(
                    ocr_data_in_range_on_page, unwanted_content)
                if len(matched_ocr_data) != 0:
                    raw_ocr_data[raw_ocr_data.index(
                        matched_ocr_data[0])][11] = AnalyserModel.BREAK_POINT_TEXT

        return raw_ocr_data

    @ staticmethod
    def _generate_questions(raw_ocr_data, question_number_sequence, pdfname, page_cnt, image_width, image_height,
                            left_bound, right_bound, top_bound, bottom_bound):
        """
        takes longest incresing sequence of longest increasing
        questions, returns answer list
        """

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

            met_break_point = False
            for page_idx in range(item[1], page_upper_bound):

                # had met break point before
                if met_break_point:
                    break

                # page is blank
                if AnalyserModel._is_blank_page(AnalyserModel._ocr_data_on_page(raw_ocr_data, page_idx)):
                    break

                data_on_page = AnalyserModel._ocr_data_in_range(
                    AnalyserModel._ocr_data_on_page(raw_ocr_data, page_idx), left_bound, right_bound, top_bound, bottom_bound)

                # question number locates on the page
                if page_idx == item[1]:
                    top_coord = item[7]
                else:
                    top_coord = top_bound

                # next question is on the page
                if idx != len(question_number_sequence) - 1 and \
                        page_idx == question_number_sequence[idx + 1][1]:
                    bottom_coord = question_number_sequence[idx + 1][7]
                else:
                    bottom_coord = AnalyserModel._last_character_bottom_coord(
                        data_on_page)

                # detect break points
                for data in AnalyserModel._ocr_data_on_page(raw_ocr_data, page_idx):
                    if data[11] == AnalyserModel.BREAK_POINT_TEXT \
                        and (data[1] != item[1]
                             or (data[1] == item[1]
                                 and data[7] > item[7] + item[9])):
                        met_break_point = True
                        bottom_coord = AnalyserModel._last_character_bottom_coord(
                            AnalyserModel._ocr_data_in_range(data_on_page, -1, -1, -1, data[7] - 1))
                        break

                # if the boxed area is empty or boxed area does not exist
                if bottom_coord <= top_coord or \
                    len(AnalyserModel._raw_ocr_data_filter
                        (AnalyserModel._ocr_data_in_range(
                            data_on_page, left_bound, right_bound, top_coord, bottom_coord
                        ))) == 0:
                    break

                coords.append({"page_num": page_idx, "left": left_bound / image_width, "right": right_bound / image_width,
                               "top": top_coord / image_height, "bottom": bottom_coord / image_height})

                text += AnalyserModel._merge_text(AnalyserModel._ocr_data_in_range(
                    data_on_page, left_bound, right_bound, top_coord, bottom_coord))

            question_list.append(AnalyserModel._make_question(
                pdfname, int(item[11]), coords, text))
        return question_list

    @ staticmethod
    def debug(question_list, pdfname, draw_box=True):
        """
        debug is what is sounds like
        """

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

            # print questions
            for item in question_list:
                for question in item["location"]:

                    if question["page_num"] == idx:
                        if draw_box:
                            new_image = cv2.rectangle(
                                new_image, (int(question["left"] * new_image.shape[1]),
                                            int(question["top"] * new_image.shape[0])),
                                (int(question["right"] * new_image.shape[1]),
                                    int(question["bottom"] * new_image.shape[0])), (0, 0, 0), 2)
                        # new_image = cv2.putText(
                        #     new_image, item["text"], (question["left"], question["bottom"]),  cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

            # write to images
            cv2.imwrite(DEBUG_DIR_PATH + "images/image" +
                        str(idx) + ".png", new_image)

            # write question data
            AnalyserModel.write_debugfile("analyser_result", question_list)

    @ staticmethod
    def write_debugfile(filename, data):
        with open(DEBUG_DIR_PATH + "json/" + str(filename) + ".json", "w") as debugfile:
            debugfile.write(json.dumps(data))
