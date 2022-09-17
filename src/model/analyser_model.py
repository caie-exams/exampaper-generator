from configuration import *

import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
from longest_increasing_subsequence import longest_increasing_subsequence
from fuzzy_match import algorithims


class AnalyserModel:

    """
    stores staticmethods that are commonly used by analysers

    this class is default for analysing quesiton papers, can be inherited
    """

    # def _generate_mcq(self, raw_ocr_data, longest_sequence, pdfname):
    #     """
    #     split and generate quesitions from longest sequence
    #     """

    #     question_list = []

    #     for idx, item in enumerate(longest_sequence):

    #         data_on_page = self.__ocr_data_in_range(
    #             self.__ocr_data_on_page(raw_ocr_data, item[1]), 175, 1550, 150, 2210)
    #         bottom_coord = -1
    #         data_in_question = []
    #         # last question of all or last question on page,
    #         # get all data up to the bottom of the most bottom word
    #         if idx == len(longest_sequence) - 1 \
    #                 or longest_sequence[idx+1][1] != item[1]:
    #             bottom_coord = self.__last_character_bottom_coord(data_on_page)
    #         # there's a gap, skips this question
    #         elif int(longest_sequence[idx + 1][11]) != int(item[11]) + 1:
    #             continue
    #         else:
    #             # this question's bottom coord = next questions's top cord
    #             bottom_coord = longest_sequence[idx + 1][7]

    #         data_in_question = self.__ocr_data_in_range(
    #             data_on_page, item[6], 1550, item[7], bottom_coord)

    #         text = self.__merge_text(data_in_question)
    #         question_list.append(self.__make_question(pdfname, int(item[11]),
    #                                                   [{"page_num": item[1], "left": 175, "right": 1550,
    #                                                     "top": item[7], "bottom": bottom_coord}], text))

    #     return question_list

    @ staticmethod
    def _scan_to_get_raw_ocr_data(images):
        """
        taking pdf path
        returns a raw ocr data and the page count

        raw ocr data format

        | num     | data        |
        | ------- | ------      |
        | 0       | leve        |
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
            raw_data = pytesseract.image_to_data(image, config=r"--psm 11")
            for item in raw_data.splitlines()[1:]:
                item_data = item.split('\t')
                item_data[:10] = map(int, item_data[:10])
                item_data[10] = float(item_data[10])
                item_data[1] = idx
                raw_ocr_data.append(item_data)

        return raw_ocr_data

    @staticmethod
    def _locate_question_numbers(raw_ocr_data, start_page, end_page, left, right, top, bottom):
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
                page, 0, left, top, bottom)
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

        limited_data = []
        for item in raw_ocr_data:
            if (left == -1 or item[6] >= left) \
                    and (right == -1 or (item[6] + item[8]) <= right) \
                and (top == -1 or item[7] >= top) \
                    and (bottom == -1 or (item[7] + item[9]) <= bottom):
                limited_data.append(item)
        return limited_data

    @ staticmethod
    def _ocr_data_on_page(raw_ocr_data, pagenum):
        """
        taking raw ocr data
        returns ocr data on specific pdf page
        """

        limited_data = []
        for item in raw_ocr_data:
            if item[1] == pagenum:
                limited_data.append(item)
        return limited_data

    @ staticmethod
    def _merge_text(raw_ocr_data):
        """
        input raw_ocr_data
        return merged text in raw ocr data
        """

        text = ""
        for word in raw_ocr_data:
            text += word[11] + " "
        return text

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
    def _make_question(pdfname,  question_number,  location, text):
        """
        question format:
        pdfname           string
        question_num      int
        location          list(dict)
              page_num    int
              left        int
              right       int
              top         int
              bottom      int
        text              string
        """

        return {"pdfname": pdfname,
                "question_num": question_number, "location": location, "text": text}
