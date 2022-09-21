# must dos

- **Train tesseract data for mcq markscheme**
- rewrite code to adapt config

- write code for categoriser
- add category keywords for testing

# To read:

- [Add text to pdf using report lab](https://stackoverflow.com/questions/1180115/add-text-to-existing-pdf-using-python)
- [Embed PDF in PDF using report lab](https://gist.github.com/marsam/7327216)
- [pdftotext](https://pypi.org/project/pdftotext/)
- [python file like objects](https://dev.to/bluepaperbirds/file-like-objects-in-python-1njf)

1. get coords of pdf
2. use pypdf2 to crop (mediabox) of pdf, save to memory using stringIO
3. use pdftext to convert cropped text to text
4. use report lab to add question num
5. use report lab to merge questions

# future todos

- fix the last mcq adds the bottom page info, by rewrite blank page detection function so it can detect any page specified in config

# minor improvements

- add control mechanism
- and multiprocessing for full core utilization
- add config logging and debugging mechanism
