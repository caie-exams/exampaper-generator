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
    def _scan_to_get_raw_ocr_data(images, tesseract_config=None):
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

        return raw_ocr_data

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

    @staticmethod
    def _generate_questions(raw_ocr_data, question_number_sequence, pdfname, page_cnt,
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

    @staticmethod
    def debug(question_list, pdfname):
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
            AnalyserModel.write_debugfile("analyser_result", question_list)

    @staticmethod
    def write_debugfile(filename, data):
        with open(DEBUG_DIR_PATH + "json/" + str(filename) + ".json", "w") as debugfile:
            debugfile.write(json.dumps(data))
