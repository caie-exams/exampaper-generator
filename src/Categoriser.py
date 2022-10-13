from model.analyser_model import AnalyserModel
from collections import OrderedDict


class Categoriser:

    @staticmethod
    def process(question_list):

        error = []

        # split qp and ms

        qp_list = []
        ms_list = []
        error_list = []

        for question in question_list:

            pdfname = question["pdfname"]

            if "qp" in pdfname:

                ms = Categoriser.find_ms(question, question_list)
                if ms is None and pdfname not in error:
                    error.append(pdfname)
                    continue

                qp_list.append(question)
                ms_list.append(ms)

        # create category

        for qp in qp_list:

    @staticmethod
    def find_ms(qp, ms_list):

        splitted_ms_pdfname = qp["pdfname"].split("_")
        splitted_ms_pdfname[2] = "ms"

        ms_pdfname = "_".join(splitted_ms_pdfname)

        ms = next(filter(lambda x: x["pdfname"] == ms_pdfname
                         and x["question_num"] == qp["question_num"], ms_list), None)

        return ms

    @staticmethod
    def decide_chapters(question_data):
        """
        \b
        return chapter occurrence 
        format:
        {"chapter name":occurrence}

        """

        text = question_data["text"]

        CHAPTER_WORDS = next(AnalyserModel.get_config(
            question_data["pdfname"], "categoriser", "chapter_keywords"), None)

        if CHAPTER_WORDS is None:
            raise (question_data["pdfname"] + "dont have keywords")

        chapter_occurrence = {}

        for key in CHAPTER_WORDS:
            cnt = 0
            for word in CHAPTER_WORDS[key]:
                if word in text:
                    cnt += 1
            if cnt != 0:
                chapter_occurrence[key] = cnt

        return chapter_occurrence


def main():

    categoriser = Categoriser()

    categoriser.process(AnalyserModel.load_debugfile("controller_results"))


if __name__ == "__main__":
    exit(main())
