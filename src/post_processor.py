from configuration import *

import PyPDF2
from fuzzysearch import find_near_matches
from func_timeout import func_timeout, FunctionTimedOut
import json


class PostProcessor():

    """
    clean the text in question and non mcq answer
    to make it ready for search by fuzzy search in
    text extracted from original pdf

    input - individual quesitons  
    output - processed individual quesitons  

    realation is one-to-one 
    """

    @ staticmethod
    def _extract_text_from_pdf(pdfname, page):
        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        with open(pdfpath, "rb") as pdf_object:
            pdf_reader = PyPDF2.PdfReader(pdf_object)
            return pdf_reader.pages[page].extractText()

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

    def process(self, question):

        extracted_text_chunk = ""
        for location in question["location"]:
            extracted_text_chunk += self._extract_text_from_pdf(
                question["pdfname"], location["page_num"])

        extracted_text_chunk = self._clean_text(extracted_text_chunk)
        question["text"] = self._clean_text(question["text"])

        word_cnt = int(len(extracted_text_chunk.split(" ")))

        try:
            match = func_timeout(
                1, find_near_matches, args=(question["text"], extracted_text_chunk), kwargs={"max_l_dist": int(word_cnt*0.2)})
        except FunctionTimedOut:
            return question

        if len(match) != 0:
            question["text"] = match[0].matched

        return [question]
