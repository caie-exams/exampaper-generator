from constants import *

import PyPDF2
import threading
import queue
from fuzzysearch import find_near_matches
from func_timeout import func_timeout, FunctionTimedOut

# job:
# clean the text to make it ready for search


class PostProcessor(threading.Thread):

    def __init__(self, callback=None, callback_args=None):
        threading.Thread.__init__(self)
        # callback is to notify master
        self.__callback = callback
        self.__callback_args = callback_args
        # threading related
        self.__active = threading.Event()
        self.__alive = threading.Event()

        # not threading related
        self.__task_queue = queue.Queue()
        self.__done_queue = queue.Queue()

    def __worker(self):
        while self.__alive.is_set():
            self.__active.wait()
            # process tasks
            task = self.get_task()
            self.__add_done(self.process(task))
            # refresh state
            self.refresh_state()

    @ staticmethod
    def __extract_text_from_pdf(pdfpath, page):
        with open(pdfpath, "rb") as pdf_object:
            pdf_reader = PyPDF2.PdfReader(pdf_object)
            return pdf_reader.pages[page].extractText()

    @ staticmethod
    def __clean_text(text):
        # replace newline and tab with space
        text = text.replace("\n", " ")
        text = text.replace("\t", " ")
        # remove multiple spaces
        text = " ".join(text.split())
        # strip leading spaces
        text = text.strip()

        return text

    def process(self, question, extracted_text):

        extracted_text_chunk = ""
        for location in question["location"]:
            extracted_text_chunk += self.__extract_text_from_pdf(
                question["pdfname"], location["page_num"])

        extracted_text_chunk = self.__clean_text(extracted_text_chunk)
        question["text"] = self.__clean_text(question["text"])

        word_cnt = int(len(extracted_text_chunk.split(" ")))

        try:
            match = func_timeout(
                1, find_near_matches, args=(question["text"], extracted_text_chunk), kwargs={"max_l_dist": int(word_cnt*0.2)})
        except FunctionTimedOut:
            return question

        if len(match) != 0:
            question["text"] = match[0].matched

        return question

    def start(self):
        self.__alive.set()
        self.refresh_state()

    def stop(self):
        self.__alive.clear()
        self.refresh_state()

    def refresh_state(self):
        if self.__task_queue.empty():
            if self.__active.is_set():
                self.__active.clear()
        if not self.__task_queue.empty():
            if not self.__active.is_set():
                self.__active.set()

    def add_task(self, question):
        self.__task_queue.put(question)
        self.refresh_state()

    def get_done(self):
        if self.__done_queue.empty():
            return None
        else:
            return self.__done_queue.get()

    def __add_done(self, question):
        self.__done_queue.put(question)
        # callback
        if self.__callback is not None:
            self.__callback(self.__callback_args)

    def __get_task(self, question):
        return self.__task_queue.get()


def main():
    pass


if __name__ == "__main__":
    exit(main())
