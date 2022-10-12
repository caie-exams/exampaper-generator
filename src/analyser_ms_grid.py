from model.analyser_model import *

import cv2
from pdf2image import convert_from_path
from longest_increasing_subsequence import longest_increasing_subsequence
from fuzzysearch import find_near_matches
from fuzzy_match import algorithims
from func_timeout import func_timeout, FunctionTimedOut


class AnalyserMSGrid(AnalyserModel):

    """
    use ocr methods to analyse mcqs that
    - with grid lines
    - are not mcq
    """

    def process(self, pdfname, tesseract_config=None):

        # load config
        UNWANTED_CONTENT_LIST = []
        for item in AnalyserModel.get_config(
                pdfname, "analyser", "unwanted_content"):
            UNWANTED_CONTENT_LIST.extend(item)

        CONTENT_AREA_PADDING = next(AnalyserModel.get_config(
            pdfname, "analyser", "question_padding"))
        if CONTENT_AREA_PADDING is None:
            CONTENT_AREA_PADDING = [0, 0, 0, 0]

        GRID_HEADER = next(AnalyserModel.get_config(
            pdfname, "analyser", "grid_header"))
        if GRID_HEADER is None:
            raise Exception("grid header is null")

        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        images = convert_from_path(pdfpath)
        page_cnt = len(images)
        images = list(map(AnalyserModel._image_preprocessing, images))

        # raw_ocr_data = AnalyserModel._scan_to_get_raw_ocr_data(
        #     images, tesseract_config)

        raw_ocr_data = []
        for idx in range(0, page_cnt):
            raw_ocr_data += AnalyserModel._pdfplumber_get_raw_data(
                pdfpath, idx, images[idx])

        start_idx, end_idx = AnalyserMSGrid._find_ms_page_range(
            raw_ocr_data, page_cnt, GRID_HEADER)
        image_width, image_height = images[start_idx].shape[1], images[start_idx].shape[0]

        left_bound, right_bound, top_bound, bottom_bound = AnalyserMSGrid._find_ms_content_boundaries(
            images[start_idx], AnalyserModel._ocr_data_on_page(raw_ocr_data,  start_idx))

        # for top bound and bottom bound may vary, so get the lim is safe
        top_bound = min([AnalyserMSGrid._find_ms_content_boundaries(
            images[idx], AnalyserModel._ocr_data_on_page(raw_ocr_data,  idx))[2]]
            for idx in range(start_idx, end_idx + 1))[0]
        bottom_bound = max([AnalyserMSGrid._find_ms_content_boundaries(
            images[idx], AnalyserModel._ocr_data_on_page(raw_ocr_data,  idx))[3]]
            for idx in range(start_idx, end_idx + 1))[0]

        # eliminate unwanted content for each page
        if UNWANTED_CONTENT_LIST is not None:
            raw_ocr_data = AnalyserModel._add_break_point(
                raw_ocr_data, UNWANTED_CONTENT_LIST, start_idx, end_idx, left_bound, right_bound, top_bound, bottom_bound)

        # find the longest non decreasing sequence

        longest_non_decreasing_sequence = longest_increasing_subsequence(
            AnalyserModel._locate_question_numbers(
                raw_ocr_data, start_idx, end_idx, left_bound, right_bound, top_bound, bottom_bound),
            False, lambda x: int(x[11]) * 1e8 + x[1] * 1e5 + x[7] * 1)

        # debug
        # AnalyserModel.write_debugfile(
        #     "question_numbers", AnalyserModel._locate_question_numbers(
        #         raw_ocr_data, start_idx, end_idx, left_bound, right_bound, top_bound, bottom_bound))
        # AnalyserModel.write_debugfile(
        #     "longest_non_decreasing_sequence", longest_non_decreasing_sequence)

        # for each duplicate question number only save the first copy
        longest_increasing_sequence = []
        for item in longest_non_decreasing_sequence:
            if item[11] not in [x[11] for x in longest_increasing_sequence]:
                longest_increasing_sequence.append(item)

        question_list = AnalyserModel._generate_questions(
            raw_ocr_data, longest_increasing_sequence,
            pdfname, page_cnt,
            image_width, image_height,
            left_bound, right_bound, top_bound, bottom_bound,
            *CONTENT_AREA_PADDING)

        return question_list

    @ staticmethod
    def _find_ms_page_range(raw_ocr_data, page_cnt, grid_header):
        """
        return the first and last page of markscheme
        """

        start_page = 0
        end_page = 0

        page_sequence = []
        for pagenum in range(0, page_cnt):
            raw_ocr_text = AnalyserModel._merge_text(
                AnalyserModel._ocr_data_on_page(raw_ocr_data, pagenum))
            if raw_ocr_text.__contains__(grid_header):
                page_sequence.append(pagenum)
            else:
                try:
                    matchs = func_timeout(1, find_near_matches,
                                          args=(grid_header,
                                                raw_ocr_text),
                                          kwargs={"max_l_dist": int(len(grid_header) * 0.2)})
                except FunctionTimedOut:
                    continue

                if len(matchs) != 0:
                    page_sequence.append(pagenum)

        if page_sequence == []:
            raise Exception("can't detect any markscheme page")

        return [page_sequence[0], page_sequence[-1]]

    @ staticmethod
    def _remove_grid_lines(image):
        """
        tessearct completely fuck up images with lots of grid lines
        so it's better to remove them before further recognizing
        """

        return cv2.bitwise_xor(image, cv2.add(*AnalyserMSGrid._get_row_and_col(image)))

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
    def _find_ms_content_boundaries(image, raw_ocr_data):
        """
        use vertical splits and question header to find boundaries
        return contours and hierarchy of the image
        """

        dilated_row, dilated_col = AnalyserMSGrid._get_row_and_col(image)

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

                # find two distinct coordinates, eliminate the others

                coordA = new_x[0]
                coordB = []
                for j, y in enumerate(new_x):
                    if abs(new_x[j][0] - coordA[0]) > 5 or abs(new_x[j][1] - coordA[1]) > 5:
                        coordB = new_x[j]
                        break

                result_contours.append([coordA, coordB])
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

        if len(vert_contours) < 1 or len(hort_contours) < 0:
            raise Exception("can't find table on page")

        return vert_contours[1], vert_contours[-1], top_coord, hort_contours[-1],


def main():

    pdfname = "9701_m16_ms_42"

    analyser = AnalyserMSGrid()
    done_data = analyser.process(pdfname)

    # print(done_data)

    print("start deugging")

    AnalyserModel.debug(done_data, pdfname, draw_box=True)


if __name__ == "__main__":
    exit(main())
