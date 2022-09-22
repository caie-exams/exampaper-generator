from configuration import *

import PyPDF2
import pdftotext
import pdf2image
import hashlib
import PIL
from io import BytesIO


class PostProcessor():

    """
    input question data,
    spit out cropped pdf, cropped image, and improve text accuracy for questions
    """

    # @ staticmethod
    # def _clean_text(text: str) -> str:
    #     # replace newline and tab with space
    #     text = text.replace("\n", " ")
    #     text = text.replace("\t", " ")
    #     # remove multiple spaces
    #     text = " ".join(text.split())
    #     # strip leading spaces
    #     text = text.strip()

    #     return text

    def process(self, question):
        original_pdffile = PostProcessor._get_pdf_file(question["pdfname"])
        original_pdffile_reader = PyPDF2.PdfReader(original_pdffile)
        pdf_width = original_pdffile_reader.pages[0].mediaBox.getWidth()
        pdf_height = original_pdffile_reader.pages[0].mediaBox.getHeight()

        text = ""
        for location in question["location"]:
            pdf_coords = PostProcessor._image_coords_to_pdf_coords(
                location["left"], location["right"], location["top"], location["bottom"], pdf_width, pdf_height)
            cropped_pdffile = PostProcessor._crop_pdf_page(
                original_pdffile, location["page_num"], pdf_coords["lower_left"], pdf_coords["lower_right"], pdf_coords["upper_left"], pdf_coords["upper_right"])
            cropped_image = PostProcessor._generate_image_from_pdf(
                cropped_pdffile)
            text += PostProcessor._extract_text_from_pdf(cropped_pdffile)
            hashed_filename = PostProcessor._generate_question_hash(
                question["pdfname"], question["question_num"], location["page_num"])
            location["hashed_filename"] = hashed_filename

            # now save the cached image and pdf
            # it's called cached because you can regenerate them anytime

            with open(DATA_DIR_PATH + "cached_pdf/" + hashed_filename + ".pdf", "wb") as cropped_pdffile_disk:
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
    def _image_coords_to_pdf_coords(left, right, top, bottom, pdf_width, pdf_height):
        """
        input locaiton percentage from question data, output coords in pdf
        """

        # left right top and bottom are all in percentage
        # image coords start from left top, pdf coords starts from left bottom

        return {"lower_left": (int(pdf_width/100 * left), int(pdf_height/100 * (100-bottom))),
                "lower_right": (int(pdf_width/100 * right), int(pdf_height/100 * (100-bottom))),
                "upper_left": (int(pdf_width/100 * left), int(pdf_height/100 * (100-top))),
                "upper_right": (int(pdf_width/100 * right), int(pdf_height/100 * (100-top)))}

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
        hasher = hashlib.sha256()
        key = str(pdfname) + str(question_num) + str(page_num)
        hasher.update(key.encode("utf-8"))
        return hasher.hexdigest()[:16]


def main():
    postprocessor = PostProcessor()
    done_data = postprocessor.process({'pdfname': '9702_s15_ms_22', 'question_num': 1, 'location': [
        {'page_num': 1, 'left': 10, 'right': 93, 'top': 9, 'bottom': 44}], 'text': None})
    print(done_data)


if __name__ == "__main__":
    exit(main())
