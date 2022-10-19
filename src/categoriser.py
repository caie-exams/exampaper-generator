from model.analyser_model import AnalyserModel
from filter import Filter
import re


class Categoriser:

    """
    categoriser takes mixed list produced by controller,
    returns a list with qp and ms pair and the categories
    """

    @staticmethod
    def process(controller_data: list):

        # get qp and ms list

        qp_list = list(Filter.get_qp(controller_data))
        ms_list = []
        for idx, qp in enumerate(qp_list):
            ms = Categoriser.find_ms_for_qp(
                qp, controller_data)
            if ms is None:
                qp_list[idx] = None
            else:
                ms_list.append(ms)

        qp_list = [qp for qp in qp_list if qp is not None]

        # get categories

        category_list = []
        for qp in qp_list:

            chapter_words = next(AnalyserModel.get_config(
                qp["pdfname"], "categoriser", "chapter_keywords"), None)

            categories = []

            if chapter_words is not None:
                categories = Categoriser.decide_chapters(qp, chapter_words)

            category_list.append(categories)

        # generate qp - ms - categories pair

        qmc_pair = [{"qp": qp_list[i], "ms":ms_list[i], "categories":category_list[i]}
                    for i in range(0, len(qp_list))]

        return qmc_pair

    @staticmethod
    def sort_by_relevance(qmc_pair_list: list, include_chapters: list, exclude_chapters: list,
                          include_keywords: list = [],  exclude_keywords: list = []):
        """
        the priority of include chapters will be high,
        the exclude chapters will be lowest
        """

        def rank(qmc_pair):

            include_chp_cnt = exclude_chp_cnt = 0
            include_kw_cnt = exclude_kw_cnt = 0

            for category in qmc_pair["categories"]:
                if category in include_chapters:
                    include_chp_cnt += 1
                if category in exclude_chapters:
                    exclude_chp_cnt += 1

            for keyword in include_keywords:
                if keyword in qmc_pair["qp"]["text"]:
                    include_kw_cnt += 1

            for keyword in exclude_keywords:
                if keyword in qmc_pair["qp"]["text"]:
                    exclude_kw_cnt += 1

            rank = include_chp_cnt / \
                len(include_chapters) * 100 - exclude_chp_cnt * 1e5
            if include_keywords != []:
                rank += include_kw_cnt / len(include_keywords) * 100
            rank -= exclude_kw_cnt * 1e5

            return rank

        return sorted(qmc_pair_list, key=lambda x: rank(x), reverse=True)

    @staticmethod
    def find_ms_for_qp(qp, ms_list):

        splitted_ms_pdfname = qp["pdfname"].split("_")
        splitted_ms_pdfname[2] = "ms"

        ms_pdfname = "_".join(splitted_ms_pdfname)

        ms = next(filter(lambda x: x["pdfname"] == ms_pdfname
                         and x["question_num"] == qp["question_num"], ms_list), None)

        return ms

    @staticmethod
    def decide_chapters(question_data, chapter_words):
        """
        \b
        return chapter occurrence
        format:
        {"chapter name":occurrence}

        """

        text = question_data["text"]

        chapter_occurrence = {}
        for key in chapter_words:
            cnt = 0
            for word in chapter_words[key]:
                if word in text:
                    cnt += 1
            if cnt != 0:
                chapter_occurrence[key] = cnt

        return chapter_occurrence


def GUIChapterSelection(pdfname):
    # get list of chapters
    chapter_keywords = next(AnalyserModel.get_config(
        pdfname, "categoriser", "chapter_keywords"), None)

    if chapter_keywords is None:
        raise Exception(pdfname + " can't find any chapter keywords")

    chapter_list = [key for key in chapter_keywords]

    # GUI

    import PySimpleGUI as sg

    layout = [
        [
            sg.Checkbox("+ ", default=False, key="+"+chapter_name),
            sg.Checkbox("- ", default=False, key="-"+chapter_name),
            sg.T(chapter_name),
            sg.T("      "),
        ]
        for chapter_name in chapter_list]

    layout += [[sg.Button('Proceed')]]

    # Setting Window
    window = sg.Window('Select chapters', layout)

    # Showing the Application, also GUI functions can be placed here.

    event, values = window.read()
    window.close()

    # Generate list

    include_list = [key[1:] for key in values if values[key] and key[0] == "+"]
    exclude_list = [key[1:] for key in values if values[key] and key[0] == "-"]

    return include_list, exclude_list


def main():

    exclude_keywords = ["eigen"]

    controller_results = AnalyserModel.load_debugfile("controller_results")
    controller_results = list(Filter.pdfname_matching(
        ".*_(qp|ms)_41.*", controller_results))

    qmc_pair_list = Categoriser.process(controller_results)

    AnalyserModel.write_debugfile("qmc_pair_list", qmc_pair_list)

    # qmc_pair_list = AnalyserModel.load_debugfile("qmc_pair_list")

    include_list, exclude_list = GUIChapterSelection(
        qmc_pair_list[0]["qp"]["pdfname"])

    results = Categoriser.sort_by_relevance(
        qmc_pair_list, include_list, exclude_list)

    results = results[:20]

    qp_list = [result["qp"] for result in results]
    ms_list = [result["ms"] for result in results]

    print(len(qp_list))

    AnalyserModel.write_debugfile("categoriser_qp", qp_list)
    AnalyserModel.write_debugfile("categoriser_ms", ms_list)


if __name__ == "__main__":
    exit(main())
