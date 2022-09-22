from configuration import *
from analyser_fixed_qn import *
from analyser_ms_grid import *
from analyser_ms_mcq import *
from post_processor import *

import os
import multiprocessing
import json


def worker(pdfname):

    print("now start with " + pdfname)

    pdfname_split = pdfname.split('_')

    if pdfname_split[2] == "qp":
        analyser = AnalyserFixedQN()
    elif pdfname_split[2] == "ms":
        # TODO: need to implement config file heere
        if pdfname_split[-1][0] == "1":
            analyser = AnalyserMSMCQ()
        else:
            analyser = AnalyserMSGrid()
    post_processor = PostProcessor()

    question_data = analyser.process(pdfname)

    processed_question_data = []
    for question in question_data:
        if question["text"] not in ["A", "B", "C", "D"]:
            try:
                processed_question_data.append(
                    post_processor.process(question))
            except:
                print(question)

    print(pdfname + " is done")

    return question_data


def main():
    # scan pdf file in the folder
    # for each pdf, scan it to obtain questions

    pool = multiprocessing.Pool(multiprocessing.cpu_count() - 1)

    PDFS_DIR = DATA_DIR_PATH + "pdf/"
    pdf_filename_list = [filename for filename in os.listdir(
        PDFS_DIR) if filename.endswith(".pdf")]

    done_data_async = []

    for pdf_filename in pdf_filename_list:

        if pdf_filename.split('_')[2] not in ["qp", "ms"]:
            continue

        pdfname = pdf_filename.split(".")[0]
        result = pool.apply_async(worker, args=(pdfname,))
        done_data_async.append(result)

    done_data = [data.get() for data in done_data_async]

    with open(DEBUG_DIR_PATH + "json/" + "controller_dump.json", "w") as debugfile:
        debugfile.write(json.dumps(done_data))


if __name__ == "__main__":
    exit(main())
