from configuration import *
from post_processor import *

import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
from longest_increasing_subsequence import longest_increasing_subsequence
from fuzzy_match import algorithims


class Analyser(ProcessorModel):

    """
    takes name of pdf and spit out questions raw data

    input - name of pdf
    output - individual quesitons

    relation is one-to-many

    this class is default for analysing quesiton papers, can be inherited
    """

    def _process(self, pdfname):

        self.config = CONFIG.get_config(pdfname)

        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        raw_ocr_data, page_cnt = self._scan(pdfpath)
        # raw_ocr_data = self.raw_ocr_data_filter(raw_ocr_data)

        # debug
        with open(DEBUG_DIR_PATH + "json/raw_ocr_data.json", "w") as debugfile:
            debugfile.write(json.dumps(raw_ocr_data))

        longest_sequence = self._locate(raw_ocr_data, page_cnt)
        # question_list = self._generate_mcq(
        #     raw_ocr_data, longest_sequence,  pdfname)
        question_list = self._generate(
            raw_ocr_data, longest_sequence, pdfname, page_cnt)
        return question_list

    @ staticmethod
    def _find_ms_page_range(raw_ocr_data):
        """
        return the first and last page of markscheme
        """

        start_page = 0
        end_page = 0

        # find the strictly increasing number of pages
        sequence = [ocr_data for ocr_data in raw_ocr_data if algorithims.levenshtein(
            ocr_data[11], "Question") >= 0.8]

        longest_sequence = longest_increasing_subsequence(
            sequence, False, lambda x: x[1])

        return [sequence[0][1], sequence[-1][1]]

    @ staticmethod
    def __find_ms_boundaries(images):
        """
        use vertical splits and question header to find boundaries
        """

        top_coord = 150
        bottom_coord = 2210
        left_coord = 175
        right_coord = 1550
        first_page = 0

        scale = 20
        idx = 0
        for image in images:

            # NOTE: The following codes are stole from
            # https://developer.aliyun.com/article/973398

            binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV)[1]

            rows, cols = binary.shape

            # 识别竖线
            scale = 20
            kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT, (1, rows // scale))
            eroded = cv2.erode(binary, kernel, iterations=1)
            dilated_row = cv2.dilate(eroded, kernel, iterations=1)

            # 识别横线:
            scale = 40
            kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT, (cols // scale, 1))
            eroded = cv2.erode(binary, kernel, iterations=1)
            dilated_col = cv2.dilate(eroded, kernel, iterations=1)

            # 将识别出来的横竖线合起来
            bitwise_and = cv2.bitwise_and(dilated_col, dilated_row)

            # 标识表格轮廓
            merge = cv2.add(dilated_col, dilated_row)

            # 获得长方形
            contours, hierarchy = cv2.findContours(
                merge, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            return contours, hierarchy

            # cv2.drawContours(image, contours, -1, (0, 0, 255), 3)

            # cv2.imwrite(DEBUG_DIR_PATH + "images/imh" +
            # str(idx) + ".png", merge)

            # idx += 1

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
        page_cnt = len(images)
        images = map(Analyser._image_preprocessing, images)

        Analyser.__find_ms_boundaries(images)

        raw_ocr_data = []
        for idx, image in enumerate(images):
            raw_data = pytesseract.image_to_data(image, config=r"--psm 11")
            for item in raw_data.splitlines()[1:]:
                item_data = item.split('\t')
                item_data[:10] = map(int, item_data[:10])
                item_data[10] = float(item_data[10])
                item_data[1] = idx
                raw_ocr_data.append(item_data)

        return [raw_ocr_data, page_cnt]

    def _locate(self, raw_ocr_data, page_cnt):
        """
        input raw ocr data
        return list of longest continous quesiton number ocr data
        """

        # find the longest sequence of questions
        question_numbers = []

        for page_idx in range(0, page_cnt):

            page = Analyser._ocr_data_on_page(raw_ocr_data, page_idx)
            num_area = Analyser._ocr_data_in_range(page, 0, 175, 150, 2210)
            for match in num_area:
                if match[10] != '-1' and match[11] != "":
                    match[11] = "".join(filter(str.isdigit, match[11]))
                    if match[11] != "" and int(match[11]) > 0:
                        question_numbers.append(match)

        longest_sequence = longest_increasing_subsequence(
            question_numbers, False, lambda x: int(x[11]))

        return longest_sequence

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

    def _generate(self, raw_ocr_data, longest_sequence, pdfname, page_cnt):
        question_list = []

        for idx, item in enumerate(longest_sequence):

            # there's a gap, skip this question
            if idx != len(longest_sequence) - 1 and \
                    int(longest_sequence[idx + 1][11]) != int(item[11]) + 1:
                continue

            coords = []
            text = ""

            # for every page if not blank page, not non-exist page,
            # get all the way down to next question or end of page

            if idx == len(longest_sequence) - 1:
                page_upper_bound = page_cnt
            else:
                page_upper_bound = longest_sequence[idx + 1][1] + 1

            for page_idx in range(item[1], page_upper_bound):

                # page is blank
                if Analyser._is_blank_page(Analyser._ocr_data_on_page(raw_ocr_data, page_idx)):
                    break

                data_on_page = Analyser._ocr_data_in_range(
                    Analyser._ocr_data_on_page(raw_ocr_data, page_idx), 175, 1550, 150, 2210)

                # first question is on the page
                if page_idx == item[1]:
                    top_coord = item[7]
                else:
                    top_coord = 150

                # last question is on the page
                if idx != len(longest_sequence) - 1 and \
                        page_idx == longest_sequence[idx + 1][1]:
                    bottom_coord = longest_sequence[idx + 1][7]
                else:
                    bottom_coord = Analyser._last_character_bottom_coord(
                        data_on_page)

                # if the boxed area is empty
                if len(Analyser._raw_ocr_data_filter(Analyser._ocr_data_in_range(data_on_page, 175, 1550, top_coord, bottom_coord))) == 0:
                    break

                coords.append({"page_num": page_idx, "left": 175, "right": 1550,
                               "top": top_coord, "bottom": bottom_coord})

                text += Analyser._merge_text(Analyser._ocr_data_in_range(
                    data_on_page, 175, 1550, top_coord, bottom_coord))

            question_list.append(Analyser._make_question(pdfname, int(item[11]),
                                                         coords, text))
        return question_list

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


# main is used for debug
def main():

    done_data = []
    pdfname = "9701_w17_ms_11"

    analyser = Analyser(done_data)
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

    images = map(Analyser._image_preprocessing, images)

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
        # for item in question_list:
        #     for question in item["location"]:

        #         if question["page_num"] == idx:
        #             new_image = cv2.rectangle(
        #                 new_image, (question["left"], question["top"]), (question["right"], question["bottom"]), (0, 0, 0), 2)
        #             # new_image = cv2.putText(
        #             #     new_image, item["text"], (question["left"], question["bottom"]),  cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

        # write to images
        cv2.imwrite(DEBUG_DIR_PATH + "images/image" +
                    str(idx) + ".png", new_image)

        # write question data
        with open(DEBUG_DIR_PATH + "json/analyser_result.json", "w") as debugfile:
            debugfile.write(json.dumps(question_list))


if __name__ == "__main__":
    exit(main())
