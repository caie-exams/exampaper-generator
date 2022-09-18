from model.analyser_model import *
from model.processor_model import *

import time
import PyPDF2


class AnalyserMSMCQ(AnalyserModel, ProcessorModel):

    """
    use ocr methods to analyse mcqs markschemes that
    - with or without grid lines

    this class won't be using tesseract or opencv,
    and will be siginificantly faster
    """

    def _process(self, pdfname):

        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        extracted_text = []
        mcq_type = "none"

        with open(pdfpath, "rb") as pdf_object:
            pdf_reader = PyPDF2.PdfReader(pdf_object)
            page_cnt = pdf_reader.numPages
            for page_idx in range(0, page_cnt):
                new_text = AnalyserMSMCQ._clean_text(
                    pdf_reader.pages[page_idx].extractText())

                if "Question Answer Marks " in new_text:
                    mcq_type = "new"
                elif "Question Number Key Question Number Key " in new_text:
                    mcq_type = "old"
                else:
                    continue
                extracted_text.append(new_text)

        if mcq_type == "new":
            return AnalyserMSMCQ._generate_new(pdfname, extracted_text)
        elif mcq_type == "old":
            return AnalyserMSMCQ._generate_old(pdfname, extracted_text)
        else:
            raise ("can't determine mcq type")

    @staticmethod
    def _generate_new(pdfname, extracted_text):

        question_list = []

        for page in extracted_text:
            str = page[page.find("Question Answer Marks ") +
                       len("Question Answer Marks "):]
            splitted = str.split(" ")
            for i in range(0, len(splitted), 3):
                number, answer = splitted[i], splitted[i+1]
                if not number.isnumeric():
                    raise ("format error, question number should be int")
                question_list.append(AnalyserModel._make_question(
                    pdfname, int(number), [], answer))

        return question_list

    @ staticmethod
    def _generate_old(pdfname, extracted_text):
        question_list = []

        for page in extracted_text:
            str = page[page.find("Question Number Key Question Number Key ") +
                       len("Question Number Key Question Number Key "):]
            splitted = str.split(" ")
            for i in range(0, len(splitted), 2):
                number, answer = splitted[i], splitted[i+1]
                if not number.isnumeric():
                    raise ("format error, question number should be int")
                question_list.append(AnalyserModel._make_question(
                    pdfname, int(number), [], answer))

        return question_list

    @ staticmethod
    def _clean_text(text: str) -> str:
        # replace newline and tab with space
        text = text.replace("\n", " ")
        text = text.replace("\t", " ")
        # remove multiple spaces
        text = " ".join(text.split())
        # strip leading spaces
        text = text.strip()
        return text


def main():

    done_data = []
    pdfname = "9701_w16_ms_11"

    analyser = AnalyserMSMCQ(done_data)
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

    AnalyserModel.debug(done_data, pdfname)


if __name__ == "__main__":
    exit(main())
