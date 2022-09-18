from model.analyser_model import *
from model.processor_model import *

import cv2
import pytesseract
from pdf2image import convert_from_path
from longest_increasing_subsequence import longest_increasing_subsequence
import time
import random


class AnalyserMS(AnalyserModel, ProcessorModel):

    """
    use ocr methods to analyse mcqs that
    - with grid lines
    - are not mcq
    """

    def _process(self, pdfname):

        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        images = convert_from_path(pdfpath)
        page_cnt = len(images)
        images = list(map(AnalyserModel._image_preprocessing, images))

        raw_ocr_data = AnalyserModel._scan_to_get_raw_ocr_data(images)
        start_idx, end_idx = AnalyserMS._find_ms_page_range(raw_ocr_data)

        left_bound, right_bound, top_bound, bottom_bound = AnalyserMS._find_ms_content_vert_boundaries(
            images[start_idx], AnalyserModel._ocr_data_on_page(raw_ocr_data,  start_idx))
        bottom_bound = max([AnalyserMS._find_ms_content_vert_boundaries(
            images[idx], AnalyserModel._ocr_data_on_page(raw_ocr_data,  idx))[3]]
            for idx in range(start_idx, end_idx + 1))[0]

        longest_non_decreasing_sequence = longest_increasing_subsequence(
            AnalyserModel._locate_question_numbers(
                raw_ocr_data, start_idx, end_idx, left_bound, right_bound, top_bound, bottom_bound),
            False, lambda x: int(x[11]) * 10000 + x[1] * 100 + x[7] * 1)

        # for each duplicate question number only save the first copy
        longest_increasing_sequence = []
        for item in longest_non_decreasing_sequence:
            if item[11] not in [x[11] for x in longest_increasing_sequence]:
                longest_increasing_sequence.append(item)

        question_list = AnalyserModel._generate_questions(raw_ocr_data, longest_increasing_sequence, pdfname,
                                                          page_cnt, left_bound, right_bound, top_bound, bottom_bound)

        return question_list

    @ staticmethod
    def _find_ms_page_range(raw_ocr_data):
        """
        return the first and last page of markscheme
        """

        start_page = 0
        end_page = 0

        # find the strictly increasing number of pages
        question_sequence = [ocr_data[1] for ocr_data in raw_ocr_data if algorithims.levenshtein(
            ocr_data[11], "Question") >= 0.8]
        answer_sequence = [ocr_data[1] for ocr_data in raw_ocr_data if algorithims.levenshtein(
            ocr_data[11], "Answer") >= 0.8]
        common_sequence = [
            page_idx for page_idx in question_sequence if page_idx in answer_sequence]

        longest_sequence = longest_increasing_subsequence(
            common_sequence, False)

        return [longest_sequence[0], longest_sequence[-1]]

    @ staticmethod
    def _remove_grid_lines(image):
        """
        tessearct completely fuck up images with lots of grid lines
        so it's better to remove them before further recognizing
        """

        return cv2.bitwise_xor(image, cv2.add(*AnalyserMS._get_row_and_col(image)))

    @ staticmethod
    def _get_row_and_col(image):
        # NOTE: The following codes are stolen from
        # https://developer.aliyun.com/article/973398
        # https://juejin.cn/post/6844904078032666631
        # the purpose is to recognise the vertical lines
        # ----------------------------------------------------

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

        # overlay = cv2.drawContours(image, contours, -1, (0, 0, 255), 3)

        return dilated_row, dilated_col

    @ staticmethod
    def _find_ms_content_vert_boundaries(image, raw_ocr_data):
        """
        use vertical splits and question header to find boundaries
        return contours and hierarchy of the image
        """

        dilated_row, dilated_col = AnalyserMS._get_row_and_col(image)

        # 获得线
        vert_contours = cv2.findContours(
            dilated_row, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        hort_contours = cv2.findContours(
            dilated_col, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        # After the veritcal lines were fetched,
        # Proceed to extract the coordinates

        def tidy_up_contours_data(contours):
            # a line has two terminal points, remove all else
            result_contours = []
            for x in [x.tolist()
                      for x in contours[0]]:
                new_x = [y[0] for y in x]
                new_new_x = new_x.copy()

                # absolute abuse of list comprehension,
                # human do not try to understand
                [[new_new_x.remove(new_x[k])
                  for k in range(j + 1, len(new_x))
                  if abs(new_x[k][0] - y[0]) < 5 and abs(new_x[k][1] - y[1]) < 5]
                 for j, y in enumerate(new_x)]

                result_contours.append(new_new_x)
            return result_contours

        vert_contours = tidy_up_contours_data(vert_contours)
        vert_contours = list(sorted(set([y[0][0] for y in [
            x for x in vert_contours if abs(x[0][0] - x[1][0]) < 5]])))

        hort_contours = tidy_up_contours_data(hort_contours)
        hort_contours = list(sorted(set([y[0][1] for y in [
            x for x in hort_contours if abs(x[0][1] - x[1][1]) < 5]])))

        # now use the raw ocr data to find the top bound

        def find_coord_under_word_question(raw_ocr_data):
            """
                input raw ocr data
                return the top coord when actually content started
                """
            question_sequence = [ocr_data[7] + ocr_data[9] for ocr_data in raw_ocr_data if algorithims.levenshtein(
                ocr_data[11], "Question") >= 0.8]

            max_apperance_cnt = -1
            max_apperance_coord = 0
            for i in range(0, len(question_sequence)):
                apperance_cnt = 1
                for j in range(i + 1, len(question_sequence)):
                    if abs(question_sequence[j] - question_sequence[i]) < 10:
                        apperance_cnt += 1
                if apperance_cnt > max_apperance_cnt:
                    max_apperance_cnt = apperance_cnt
                    max_apperance_coord = question_sequence[i]

            return max_apperance_coord

        coord_under_question = find_coord_under_word_question(raw_ocr_data)
        top_coord = next(
            filter(lambda x: x > coord_under_question, hort_contours), None)

        # vertically: left of box, left of content, ... , right of box
        # horizontally: top of content, bottom of box

        return vert_contours[1], vert_contours[-1], top_coord, hort_contours[-1],


def main():

    done_data = []
    pdfname = "9701_w17_ms_22"

    analyser = AnalyserMS(done_data)
    analyser.start()
    analyser.add_task(pdfname)
    isrunning = True
    analyser.stop()
    while isrunning:
        isalive, isrunning, leng = analyser.status()
        print(isalive, isrunning, leng)
        time.sleep(1)

    # print(done_data)

    print("start deugging")

    AnalyserModel.debug(done_data, pdfname)


if __name__ == "__main__":
    exit(main())
