import tabula
import PyPDF2

pdfpath = "/Users/justin/Codes/ocr/data/pdf/9701_w17_ms_11.pdf"

# content = tabula.read_pdf(pdfpath, pages=2, output_format="json", stream=False)
content = tabula.read_pdf(pdfpath, pages=2, stream=False)

print(content)


pdfpath = "/Users/justin/Codes/ocr/data/pdf/9701_w16_ms_11.pdf"

with open(pdfpath, "rb") as pdf_object:
    pdf_reader = PyPDF2.PdfReader(pdf_object)
    print(pdf_reader.pages[1].extractText())
