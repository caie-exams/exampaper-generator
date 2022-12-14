from configuration import *
from analyser_fixed_qn import *
from analyser_ms_grid import *
from analyser_ms_mcq import *
from post_processor import *

import os
import multiprocessing
import json


"""
controller scans pdf in directory, process 
and returns a list of data of all qp and ms 
in the directory
"""


def worker(pdfname):
    # load config

    print("now start with " + pdfname)

    analyser_selection = next(AnalyserModel.get_config(
        pdfname, "controller", "analyser_selection"))

    if analyser_selection is None:
        raise Exception("can't specify analyser")
    elif analyser_selection == "fixed_qn":
        analyser = AnalyserFixedQN()
    elif analyser_selection == "ms_mcq":
        analyser = AnalyserMSMCQ()
    elif analyser_selection == "ms_grid":
        analyser = AnalyserMSGrid()

    post_processor = PostProcessor()

    question_data = analyser.process(pdfname, "-l arial --psm 12")

    processed_question_data = []
    for question in question_data:
        if question["text"] not in ["A", "B", "C", "D"]:
            processed_question_data.append(
                post_processor.process(question))

    print(pdfname + " is done")

    return question_data


def main():
    # scan pdf file in the folder
    # for each pdf, scan it to obtain questions

    pool = multiprocessing.Pool(multiprocessing.cpu_count() - 1)

    PDFS_DIR = DATA_DIR_PATH + "pdf/"

    pdf_filename_list = [filename for filename in os.listdir(
        PDFS_DIR) if filename.endswith(".pdf")]

    done_data_async = {}

    for pdf_filename in pdf_filename_list:

        pdfname = pdf_filename.split(".")[0]
        is_included = next(AnalyserModel.get_config(
            pdfname, "controller", "is_included"), None)
        if is_included is not None and is_included:
            result = pool.apply_async(worker, args=(pdfname,))
            done_data_async[pdfname] = result

    done_data = []
    error_list = {}
    for key in done_data_async:
        try:
            got_data = done_data_async[key].get()
            done_data.extend(got_data)
        except Exception as e:
            error_list[key] = str(e)

    with open(DEBUG_DIR_PATH + "json/" + "controller_results.json", "w") as debugfile:
        debugfile.write(json.dumps(done_data))

    with open(DEBUG_DIR_PATH + "json/" + "controller_errors.json", "w") as debugfile:
        debugfile.write(json.dumps(error_list))


if __name__ == "__main__":
    exit(main())
