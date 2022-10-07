import pdfplumber

with pdfplumber.open("data/pdf/9608_w20_qp_12.pdf") as pdf:
    page = pdf.pages[1]
    print(page.extract_words())
