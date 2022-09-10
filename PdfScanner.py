# PdfScanner
# Input the path of PDF file, output

from constants import *

import PyPDF2
import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
import json
from longest_increasing_subsequence import longest_increasing_subsequence


class PdfScanner:
    def __init__(self, path):
        self.path = path
        self.pdf_object = open(path, "rb")
        self.pdf_reader = PyPDF2.PdfReader(self.pdf_object)

    def process(self):
        print("start analyse!")
        self.analyse()
        print("start prepare!")
        self.prepare()
        print("start locate!")
        self.locate()

    # get basic information from pdf and config file
    def analyse(self):
        self.total_page_cnt = self.pdf_reader.numPages
        pass

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
            if type(item) != list:
                print(item)
                print(limited_data)
                dumped = json.dumps(limited_data)
                with open(DEBUG_DIR_PATH + "debug.json", "w") as debugf:
                    debugf.write(dumped)
                input()
                continue
            if (left == -1 or item[6] >= left) \
                    and (right == -1 or (item[6] + item[8]) <= right) \
                and (top == -1 or item[7] >= top) \
                    and (bottom == -1 or (item[7] + item[9]) <= bottom):
                limited_data.append(item)
        return limited_data

    # form a list of question on given page
    def __ocr_data_on_page(self, data, page):
        limited_data = []
        for item in data:
            if item[1] == page:
                limited_data.append(item)
        return limited_data

    # test if BLANK PAGE is present on the page
    def __is_blank_page(self, pagenum):
        data = self.__ocr_data_in_range(
            self.raw_ocr_data[pagenum], -1, -1, 160, 220)
        for item in data:
            if "BLANK" in item or "PAGE" in item:
                return True
        return False

    # locate questions to coordinates on each page

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

        longest_sequence = longest_increasing_subsequence(
            question_numbers, False, lambda x: int(x[11]))

        # merge text in data
        def merge_text(data):
            text = ""
            for word in data:
                text += word[11]

        # obtain the most bottom character's bottom coords
        def last_character_bottom_cords(data):
            ans = -1
            for item in data:
                ans = max(ans, item[7] + item[9])
            return ans

        # devide into questions
        #
        # question format:
        # pdfname           string
        # pagenum           int
        # coordinates       list(dict)
        #       left        int
        #       right       int
        #       top         int
        #       bottom      int
        # text              string

        return

        question_list = {}
        for idx, item in enumerate(longest_sequence):
            if idx == len(longest_sequence) - 1:
                # bottom_coord = last_character_bottom_cords(
                self.__ocr_data_in_range()

    def __compare(self):
        pass

    def debug(self):

        # for idx, image in enumerate(self.images):
        #     print(idx)
        #     self.__ocr_data_in_range(self.__ocr_data_on_page(
        #         self.raw_ocr_data, idx), 0, 175, 0, 2200)

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
            for item in self.__ocr_data_in_range(self.__ocr_data_on_page(self.raw_ocr_data, idx), 0, 175, 0, 2200):
                # for line in enumerate(self.test_list):
                if item[1] == idx:
                    image = cv2.rectangle(
                        image, (item[6], item[7]), (item[6] + item[8], item[7] + item[9]), (0, 0, 100), 2)
                    image = cv2.putText(
                        image, item[11], (item[6] + item[8], item[7] + item[9] + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

            # test if blank page
            if self.__is_blank_page(idx):
                image = cv2.putText(
                    image, "BLANK PAGE DETECTED", (int(image.shape[1]/2), int(image.shape[0]/2)), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

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
