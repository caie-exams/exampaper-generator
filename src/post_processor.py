from configuration import *

import PyPDF2
import pdftotext
import pdf2image
import PIL
from io import BytesIO
from decimal import Decimal


class PostProcessor():

    """
    input question data,
    spit out cropped pdf, cropped image, and improve text accuracy for questions  
    plus it detects certain excessive content (like periodic table) and kick them out 
    """

    def process(self, question):
        original_pdffile = PostProcessor._get_pdf_file(question["pdfname"])
        original_pdffile_reader = PyPDF2.PdfReader(original_pdffile)

        text = ""
        for location in question["location"]:
            upperright_x = original_pdffile_reader.pages[location["page_num"]].mediaBox.getUpperRight_x(
            )
            upperright_y = original_pdffile_reader.pages[location["page_num"]].mediaBox.getUpperRight_y(
            )
            orientation = original_pdffile_reader.getPage(
                location["page_num"]).get('/Rotate')

            pdf_coords = PostProcessor._image_coords_to_pdf_coords(
                location["left"], location["right"], location["top"], location["bottom"], upperright_x, upperright_y, orientation)

            cropped_pdffile = PostProcessor._crop_pdf_page(
                original_pdffile, location["page_num"], pdf_coords["lower_left"], pdf_coords["lower_right"], pdf_coords["upper_left"], pdf_coords["upper_right"])
            text += PostProcessor._extract_text_from_pdf(cropped_pdffile)

            cropped_image = PostProcessor._generate_image_from_pdf(
                cropped_pdffile)

            hashed_filename = PostProcessor._generate_question_hash(
                question["pdfname"], question["question_num"], location["page_num"])
            location["hashed_filename"] = hashed_filename

            # now save the cached image and pdf
            # it's called cached because you can regenerate them anytime

            with open(DATA_DIR_PATH + "cached_pdf/" + hashed_filename + ".pdf", "wb") as cropped_pdffile_disk:
                cropped_pdffile.seek(0)
                cropped_pdffile_disk.write(cropped_pdffile.getbuffer())
                cropped_pdffile.close()
            cropped_image.save(DATA_DIR_PATH + "cached_image/" +
                               hashed_filename + ".png", format="png")

        original_pdffile.close()
        question["text"] = text
        return question

    @ staticmethod
    def _get_pdf_file(pdfname):
        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
        pdffile = open(pdfpath, "rb")
        return pdffile

    @ staticmethod
    def _image_coords_to_pdf_coords(left, right, top, bottom, upperright_x, upperright_y, orientation=None) -> dict:
        """
        input locaiton percentage from question data, output coords in pdf
        """

        # left right top and bottom are all in percentage
        # image coords start from left top, pdf coords starts from left bottom

        # if the page is landscape, the coords of pdf stays portrait

        if left < 0 or left > 1 \
                or right < 0 or right > 1 \
                or top < 0 or top > 1 \
                or bottom < 0 or bottom > 1:
            raise Exception("coords not correct")

        if orientation == 90:
            top, bottom, left, right = left, right, bottom, top
        if orientation == 270:
            top, bottom, left, right = right, left, top, bottom

        return {"lower_left": (upperright_x * Decimal(left), upperright_y * Decimal(1-bottom)),
                "lower_right": (int(upperright_x * Decimal(right)), upperright_y * Decimal(1-bottom)),
                "upper_left": (upperright_x * Decimal(left), upperright_y * Decimal(1-top)),
                "upper_right": (upperright_x * Decimal(right), upperright_y * Decimal(1-top))}

    @ staticmethod
    def _crop_pdf_page(pdffile,  pagenum: int, lower_left: tuple, lower_right: tuple, upper_left: tuple, upper_right: tuple) -> BytesIO:
        """
        input pdf fileobejct  and location, output a file object of a cropped page in the file
        """
        pdf_object = PyPDF2.PdfFileReader(pdffile)
        page = pdf_object.getPage(pagenum)

        page.mediaBox.lower_left = lower_left
        page.mediaBox.lower_right = lower_right
        page.mediaBox.upper_left = upper_left
        page.mediaBox.upper_right = upper_right

        # page.mediaBox.upper_left = upper_left
        # print(page.mediaBox.lower_right[0], page.mediaBox.lower_right[1])

        output_writer = PyPDF2.PdfFileWriter()
        output_writer.add_page(page)

        output_file = BytesIO()
        output_writer.write(output_file)
        output_file.seek(0)
        return output_file

    @ staticmethod
    def _extract_text_from_pdf(pdffile: BytesIO, page=0) -> str:
        pdf_reader = pdftotext.PDF(pdffile)
        pdffile.seek(0)
        return pdf_reader[page]

    @ staticmethod
    def _generate_image_from_pdf(pdffile: BytesIO, page=0) -> PIL:
        image = pdf2image.convert_from_bytes(pdffile.read())[page]
        pdffile.seek(0)
        return image

    @ staticmethod
    def _generate_question_hash(pdfname, question_num, page_num):
        """
        use pdfname, question_num and page_num you can locate a question!
        """
        # hasher = hashlib.sha256()
        # key = str(pdfname) + str(question_num) + str(page_num)
        # hasher.update(key.encode("utf-8"))
        # return hasher.hexdigest()[:16]

        # the fuck, no need to hash
        return "_".join([pdfname, str(question_num), str(page_num)])


def main():
    postprocessor = PostProcessor()
    DATA = [{
        "pdfname": "9608_s15_qp_41",
        "question_num": 1,
        "location": [
            {
                "page_num": 2,
                "left": 0.20557436517533253,
                "right": 0.9401451027811366,
                "top": 0.20231279217726075,
                "bottom": 0.6643823384640694,
                "hashed_filename": "9608_s15_qp_41_1_2"
            }
        ],
        "text": "1\n\nA turnstile is a gate which is in a locked state. To open it and pass through, a customer inserts\na coin into a slot on the turnstile. The turnstile then unlocks and allows the customer to push the\nturnstile and pass through the gate.\nAfter the customer has passed through, the turnstile locks again. If a customer pushes the turnstile\nwhile it is in the locked state, it will remain locked until another coin is inserted.\nThe turnstile has two possible states: locked and unlocked. The transition from one state to\nanother is as shown in the table below.\nCurrent state\n\nEvent\n\nNext state\n\nLocked\n\nInsert coin\n\nUnlocked\n\nLocked\n\nPush\n\nLocked\n\nUnlocked\n\nAttempt to insert coin\n\nUnlocked\n\nUnlocked\n\nPass through\n\nLocked\n\nComplete the state transition diagram for the turnstile:\n\n..............................\n\n..............................\n\n..............................\n\n...........................\n\n..............................\nstart\n\n..............................\n\n[5]\n\n\f"
    }, ]
    for data in DATA:
        done_data = postprocessor.process(data)
        # print(done_data)


if __name__ == "__main__":
    exit(main())
