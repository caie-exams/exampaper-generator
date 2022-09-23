from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
import pdftotext

# pdf_file = PdfFileReader(
#     open("/Users/justin/Codes/ocr/data/pdf/0620_s20_qp_21.pdf", "rb"))
# page = pdf_file.getPage(0)


# # page.bleedBox.lowerRight = (10, 20)
# # page.bleedBox.lowerLeft = (30,
# #                            40)
# # page.bleedBox.upperRight = (
# #     50, 60)
# # page.bleedBox.upperLeft = (70,
# #                            80)

# page.mediaBox.upperRight = (500, -1)
# page.mediaBox.upperLeft = (70, 800)


# # page.cropbox.lowerRight = (10, 20)
# # page.cropbox.lowerLeft = (30,
# #                           40)
# # page.cropbox.upperRight = (
# #     50, 60)
# # page.cropbox.upperLeft = (70,
# #                           80)

# output = PdfFileWriter()
# output.addPage(page)

# with open("out.pdf", "wb") as out_f:
#     output.write(out_f)

with open("/Users/justin/Codes/ocr/data/cached_pdf/9701_w18_ms_43_3_7.pdf", "rb") as f:
    pdf = pdftotext.PDF(f)
    print(pdf[0])
