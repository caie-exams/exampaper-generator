from constants import *

import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
import json
from os.path import basename, splitext
from longest_increasing_subsequence import longest_increasing_subsequence
from jsonmerge import merge

# takes a pdf and output a list of questions with basically raw data
# after some tidy up this could be a parent class


class Analyser:

    def __init__(self, path):
        self.path = path
        self.pdf_name = splitext(basename(self.path))[0]

        # load settings
        self.settings = self.load_settings()
        pytesseract.__loader__

    def process(self):
        print("start prepare!")
        images, raw_ocr_data, total_page_cnt = self.prepare()
        print("start locate!")
        longest_sequence = self.locate(raw_ocr_data, total_page_cnt)
        print("start split!")
        question_list = self.split(raw_ocr_data, longest_sequence)
        return question_list

    def load_settings(self):
        self.subject_num = self.pdf_name.split('_')[0]
        try:
            with open(SUBJECT_SETTINGS + self.subject_num + ".json", "r") as subject_json:
                subject_specifc_settings = json.loads(subject_json.read())
        except IOError as e:
            print("warning: " + self.subject_num + ".json" + " not found.")

        with open(SUBJECT_SETTINGS + DEFAULT_FILE, "r") as defualt_json:
            default_settings = json.loads(defualt_json.read())

        settings = merge(default_settings, subject_specifc_settings)
        print(settings)

    # split pdf into pages of raw_ocr_texts
    # for ocr texts, format is
    # 0     1           2           3       4           5           6       7   8       9       10      11
    # level page_num    block_num   par_num line_num    word_num    left    top width   height  conf    text

    def prepare(self):
        # scan to get rough ocr text
        images = convert_from_path(self.path)
        raw_ocr_data = []
        for idx, image in enumerate(images):
            print("preparing page:", idx)
            pytesseract
            raw_data = pytesseract.image_to_data(image)
            for item in raw_data.splitlines()[1:]:
                item_data = item.split('\t')
                item_data[:10] = map(int, item_data[:10])
                item_data[10] = float(item_data[10])
                item_data[1] = idx
                raw_ocr_data.append(item_data)

        total_page_cnt = len(images)

        def pil2cv2(img):
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        images = map(pil2cv2, images)

        return [images, raw_ocr_data, total_page_cnt]

    # return ocr data in the area

    def __ocr_data_in_range(self, data, left, right, top,  bottom):
        limited_data = []
        for item in data:
            if (left == -1 or item[6] >= left) \
                    and (right == -1 or (item[6] + item[8]) <= right) \
                and (top == -1 or item[7] >= top) \
                    and (bottom == -1 or (item[7] + item[9]) <= bottom):
                limited_data.append(item)
        return limited_data

    # form a list of question on given page
    def __ocr_data_on_page(self, data, pagenum):
        limited_data = []
        for item in data:
            if item[1] == pagenum:
                limited_data.append(item)
        return limited_data

    # test if BLANK PAGE is present on the page
    def __is_blank_page(self, pagenum):
        data = self.__ocr_data_in_range(
            self.__ocr_data_on_page(self.raw_ocr_data, pagenum), -1, -1, 160, 220)
        for item in data:
            if "BLANK" in item or "PAGE" in item:
                return True
        return False

    # locate question numbers to coordinates on each page
    def locate(self, raw_ocr_data, total_page_cnt):

        # find the longest sequence of questions
        question_numbers = []

        for page_idx in range(0, total_page_cnt):
            page = self.__ocr_data_on_page(raw_ocr_data, page_idx)
            num_area = self.__ocr_data_in_range(page, 0, 175, 150, 2200)
            for match in num_area:
                if match[11] != '-1' and match[11] != "":
                    match[11] = "".join(filter(str.isdigit, match[11]))
                    if match[11] != "" and int(match[11]) > 0:
                        question_numbers.append(match)

        longest_sequence = longest_increasing_subsequence(
            question_numbers, False, lambda x: int(x[11]))
        return longest_sequence

    # merge text in data

    def __merge_text(self, data):
        text = ""
        for word in data:
            text += word[11] + " "
        return text

    # obtain the most bottom character's bottom coords
    def __last_character_bottom_cords(self, data):
        ans = -1
        for item in data:
            ans = max(ans, item[7] + item[9])
        return ans

    # question format:
    # pdfname           string
    # question_num      int
    # location          list(dict)
    #       page_num    int
    #       left        int
    #       right       int
    #       top         int
    #       bottom      int
    # text              string
    def __make_question(self,  question_number,  location, text):
        return {"pdfname": self.pdf_name,
                "question_num": question_number, "location": location, "text": text}

    # split quesitons to each box
    def split(self, raw_ocr_data, longest_sequence):
        question_list = []

        for idx, item in enumerate(longest_sequence):

            data_on_page = self.__ocr_data_in_range(
                self.__ocr_data_on_page(raw_ocr_data, item[1]), 175, 1550, 150, 2200)
            bottom_coord = -1
            data_in_question = []
            if idx == len(longest_sequence) - 1 \
                    or longest_sequence[idx+1][1] != item[1]:
                # last question of all or last question on page,
                # get all data up to the bottom of the most bottom word
                print(item[11])
                bottom_coord = self.__last_character_bottom_cords(data_on_page)
            elif int(longest_sequence[idx + 1][11]) != int(item[11]) + 1:
                # there's a gap, skips this question
                continue
            else:
                # this question's bottom coord = next questions's top cord
                bottom_coord = longest_sequence[idx + 1][7]

            data_in_question = self.__ocr_data_in_range(
                data_on_page, item[6], 1550, item[7], bottom_coord)

            text = self.__merge_text(data_in_question)
            question_list.append(self.__make_question(int(item[11]),
                                                      [{"page_num": item[1], "left": 175, "right": 1550,
                                                        "top": item[7], "bottom": bottom_coord}], text))

        return question_list

# def debug(self, images, extracted_data, question_list):

#     for idx, image in enumerate(images):

#         new_image = image

#         # print line
#         new_image = cv2.line(
#             new_image, (175, 0), (175, new_image.shape[0]), (0, 100, 0), 2)
#         new_image = cv2.line(new_image, (0, 2200),
#                                 (new_image.shape[1], 2200), (0, 100, 0), 2)
#         new_image = cv2.line(new_image, (0, 150),
#                                 (new_image.shape[1], 150), (0, 100, 0), 2)
#         new_image = cv2.line(new_image, (1550, 0),
#                                 (1550, new_image.shape[0]), (0, 100, 0), 2)

#         # print questions
#         for item in question_list:
#             for question in item["location"]:

#                 if question["page_num"] == idx:
#                     new_image = cv2.rectangle(
#                         new_image, (question["left"], question["top"]), (question["right"], question["bottom"]), (0, 0, 100), 2)
#                     new_image = cv2.putText(
#                         new_image, item["text"], (question["left"], question["bottom"]),  cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

#         # write to images
#         cv2.imwrite(DEBUG_DIR_PATH + "image" +
#                     str(idx) + ".png", new_image)

#         # write to file
#         extracted_json = json.dumps(extracted_data)
#         with open(DEBUG_DIR_PATH + "debug.json", "w") as debugfile:
#             debugfile.write(extracted_json)


# main is used for debug
def main():
    print(DATA_DIR_PATH + "pdf/0620_s20_qp_11.pdf")
    pdfScanner = Analyser(DATA_DIR_PATH + "pdf/0620_s20_qp_11.pdf")
    print(pdfScanner.process())


if __name__ == "__main__":
    exit(main())
