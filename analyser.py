from constants import *
from post_processor import *

import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
import json
from os.path import basename, splitext
from longest_increasing_subsequence import longest_increasing_subsequence
from jsonmerge import merge


class Analyser(ProcessorModel):

    """
    takes name of pdf and spit out questions raw data

    input - name of pdf  
    output - individual quesitons  

    relation is one-to-many
    """

    def _process(self, pdfname):
        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        raw_ocr_data, page_cnt = self._scan(pdfpath)
        question_list = self._locate(raw_ocr_data, page_cnt, pdfname)
        return question_list

    # def load_settings(self):
    #     self.subject_num = self.pdf_name.split('_')[0]
    #     try:
    #         with open(SUBJECT_SETTINGS + self.subject_num + ".json", "r") as subject_json:
    #             subject_specifc_settings = json.loads(subject_json.read())
    #     except IOError as e:
    #         print("warning: " + self.subject_num + ".json" + " not found.")

    #     with open(SUBJECT_SETTINGS + DEFAULT_FILE, "r") as defualt_json:
    #         default_settings = json.loads(defualt_json.read())

    #     settings = merge(default_settings, subject_specifc_settings)
    #     print(settings)

    def _scan(self, pdfpath):
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

        images = convert_from_path(pdfpath)
        raw_ocr_data = []
        for idx, image in enumerate(images):
            pytesseract
            raw_data = pytesseract.image_to_data(image)
            for item in raw_data.splitlines()[1:]:
                item_data = item.split('\t')
                item_data[:10] = map(int, item_data[:10])
                item_data[10] = float(item_data[10])
                item_data[1] = idx
                raw_ocr_data.append(item_data)

        page_cnt = len(images)

        def pil2cv2(img):
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        images = map(pil2cv2, images)

        return [raw_ocr_data, page_cnt]

    def _locate(self, raw_ocr_data, page_cnt, pdfname):
        """
        input raw ocr data 
        return list of questions
        """

        # find the longest sequence of questions
        question_numbers = []

        for page_idx in range(0, page_cnt):
            page = self.__ocr_data_on_page(raw_ocr_data, page_idx)
            num_area = self.__ocr_data_in_range(page, 0, 175, 150, 2200)
            for match in num_area:
                if match[11] != '-1' and match[11] != "":
                    match[11] = "".join(filter(str.isdigit, match[11]))
                    if match[11] != "" and int(match[11]) > 0:
                        question_numbers.append(match)

        longest_sequence = longest_increasing_subsequence(
            question_numbers, False, lambda x: int(x[11]))

        # split and generate questions

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
                bottom_coord = self.__last_character_bottom_coord(data_on_page)
            elif int(longest_sequence[idx + 1][11]) != int(item[11]) + 1:
                # there's a gap, skips this question
                continue
            else:
                # this question's bottom coord = next questions's top cord
                bottom_coord = longest_sequence[idx + 1][7]

            data_in_question = self.__ocr_data_in_range(
                data_on_page, item[6], 1550, item[7], bottom_coord)

            text = self.__merge_text(data_in_question)
            question_list.append(self.__make_question(pdfname, int(item[11]),
                                                      [{"page_num": item[1], "left": 175, "right": 1550,
                                                        "top": item[7], "bottom": bottom_coord}], text))

        return question_list

    @staticmethod
    def __ocr_data_in_range(raw_ocr_data, left, right, top,  bottom):
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

    @staticmethod
    def __ocr_data_on_page(raw_ocr_data, pagenum):
        """
        taking raw ocr data   
        returns ocr data on specific pdf page  
        """

        limited_data = []
        for item in raw_ocr_data:
            if item[1] == pagenum:
                limited_data.append(item)
        return limited_data

    @staticmethod
    def __merge_text(raw_ocr_data):
        """
        input raw_ocr_data  
        return merged text in raw ocr data
        """

        text = ""
        for word in raw_ocr_data:
            text += word[11] + " "
        return text

    @staticmethod
    def __last_character_bottom_coord(raw_ocr_data):
        """
        input raw ocr data  
        return last character on ocr data's bottom coord

        used to find the last quesiton on page
        """
        ans = -1
        for item in raw_ocr_data:
            ans = max(ans, item[7] + item[9])
        return ans

    # # test if BLANK PAGE is present on the page
    # def __is_blank_page(self, pagenum):
    #     data = self.__ocr_data_in_range(
    #         self.__ocr_data_on_page(self.raw_ocr_data, pagenum), -1, -1, 160, 220)
    #     for item in data:
    #         if "BLANK" in item or "PAGE" in item:
    #             return True
    #     return False

    @staticmethod
    def __make_question(pdfname,  question_number,  location, text):
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

    done_data = []

    analyser = Analyser(done_data)
    analyser.start()
    analyser.add_task("0620_s20_qp_11")
    isrunning = True
    analyser.stop()
    while isrunning:
        isalive, isrunning, leng = analyser.status()
        print(isalive, isrunning, leng)
        time.sleep(1)

    print(done_data)


if __name__ == "__main__":
    exit(main())
