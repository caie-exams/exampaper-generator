# PdfScanner
# Input the path of PDF file, output

from constants import *

import PyPDF2
import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
import json
from os.path import basename, splitext
from longest_increasing_subsequence import longest_increasing_subsequence


class PdfScanner:
    def __init__(self, path):
        # init basic vars
        self.path = path
        self.pdf_object = open(path, "rb")
        self.pdf_reader = PyPDF2.PdfReader(self.pdf_object)
        self.question_list = []

        # init analysic vas
        self.total_page_cnt = self.pdf_reader.numPages

    def process(self):
        print("loading settings")
        # self.load_settings()
        print("start prepare!")
        self.prepare()
        print("start locate!")
        self.locate()
        print("start split!")
        self.split_mcq()

    # split pdf into pages of raw_ocr_texts
    # for ocr texts, format is
    # 0     1           2           3       4           5           6       7   8       9       10      11
    # level page_num    block_num   par_num line_num    word_num    left    top width   height  conf    text

    def prepare(self):
        # scan to get rough ocr text
        self.images = convert_from_path(self.path)
        self.raw_ocr_data = []
        self.chunk_ocr_data = []
        for idx, image in enumerate(self.images):
            print("preparing page:", idx)
            pytesseract
            raw_data = pytesseract.image_to_data(image)
            for item in raw_data.splitlines()[1:]:
                item_data = item.split('\t')
                item_data[:10] = map(int, item_data[:10])
                item_data[10] = float(item_data[10])
                item_data[1] = idx
                self.raw_ocr_data.append(item_data)

        def pil2cv2(img):
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        self.images = map(pil2cv2, self.images)

        # extract precise text from doc
        # self.extracted_text = []
        # for page in self.pdfReader.pages:
        #     self.extracted_text.append(page.extractText())

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
    def locate(self):

        # find the longest sequence of questions
        question_numbers = []

        for page_idx in range(0, self.total_page_cnt):
            page = self.__ocr_data_on_page(self.raw_ocr_data, page_idx)
            num_area = self.__ocr_data_in_range(page, 0, 175, 150, 2200)
            for match in num_area:
                if match[11] != '-1' and match[11] != "":
                    match[11] = "".join(filter(str.isdigit, match[11]))
                    if match[11] != "" and int(match[11]) > 0:
                        question_numbers.append(match)

        self.longest_sequence = longest_increasing_subsequence(
            question_numbers, False, lambda x: int(x[11]))

    # merge text in data

    def __merge_text(self, data):
        text = ""
        for word in data:
            text += word[11].lower() + " "
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
    def __add_question(self, question_number,  location, text):
        new_question = {"pdfname": splitext(basename(self.path))[
            0], "question_num": question_number, "location": location, "text": text}
        self.question_list.append(new_question)

    # split quesitons to each box
    def split_mcq(self):
        for idx, item in enumerate(self.longest_sequence):

            data_on_page = self.__ocr_data_in_range(
                self.__ocr_data_on_page(self.raw_ocr_data, item[1]), 175, 1550, 150, 2200)
            bottom_coord = -1
            data_in_question = []
            if idx == len(self.longest_sequence) - 1 \
                    or self.longest_sequence[idx+1][1] != item[1]:
                # last question of all or last question on page,
                # get all data up to the bottom of the most bottom word
                print(item[11])
                bottom_coord = self.__last_character_bottom_cords(data_on_page)
            elif int(self.longest_sequence[idx + 1][11]) != int(item[11]) + 1:
                # there's a gap, skips this question
                continue
            else:
                # this question's bottom coord = next questions's top cord
                bottom_coord = self.longest_sequence[idx + 1][7]

            data_in_question = self.__ocr_data_in_range(
                data_on_page, item[6], 1550, item[7], bottom_coord)

            text = self.__merge_text(data_in_question)
            self.__add_question(int(item[11]), [{"page_num": item[1], "left": item[6],
                                "right": 1550, "top": item[7], "bottom": bottom_coord}], text)

    def debug(self):

        for idx, image in enumerate(self.images):

            # print line
            image = cv2.line(
                image, (175, 0), (175, image.shape[0]), (0, 100, 0), 2)
            image = cv2.line(image, (0, 2200),
                             (image.shape[1], 2200), (0, 100, 0), 2)
            image = cv2.line(image, (0, 150),
                             (image.shape[1], 150), (0, 100, 0), 2)
            image = cv2.line(image, (1550, 0),
                             (1550, image.shape[0]), (0, 100, 0), 2)

            # print boxes
            # for item in self.__ocr_data_in_range(self.__ocr_data_on_page(self.test_list, idx), 0, -1, 0, -1):
            #     # for line in enumerate(self.test_list):
            #     if item[1] == idx:
            #         image = cv2.rectangle(
            #             image, (item[6], item[7]), (item[6] + item[8], item[7] + item[9]), (0, 0, 100), 2)
            #         image = cv2.putText(
            #             image, item[11], (item[6] + item[8], item[7] + item[9] + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
            for item in self.question_list:
                for question in item["location"]:

                    if question["page_num"] == idx:
                        image = cv2.rectangle(
                            image, (question["left"], question["top"]), (question["right"], question["bottom"]), (0, 0, 100), 2)
                        image = cv2.putText(
                            image, item["text"], (question["left"], question["bottom"]),  cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

            # test if blank page
            # if self.__is_blank_page(idx):
            #     image = cv2.putText(
            #         image, "BLANK PAGE DETECTED", (int(image.shape[1]/2), int(image.shape[0]/2)), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

            cv2.imwrite(DEBUG_DIR_PATH + "image" + str(idx) + ".png", image)

    def __del__(self):
        self.pdf_object.close()


print(DATA_DIR_PATH + "pdf/0620_s20_qp_11.pdf")
pdfScanner = PdfScanner(DATA_DIR_PATH + "pdf/0620_s20_qp_11.pdf")
pdfScanner.process()
raw_ocr_data = json.dumps(pdfScanner.raw_ocr_data)
file2 = open(DEBUG_DIR_PATH + "raw_ocr_data.json", "w")
file2.write(raw_ocr_data)
file2.close()
print("start debug!")
pdfScanner.debug()

# must dos
# - add config to support more types other than mcq
# - add support to mark schemes
# - fix the last mcq adds the bottom page info

# major improvements
# - use fuzzy search to make the text more accurate

# minor improvements
# - reconstruct the code to use multithreading to speed up the process
