<p align="center">
    <img src="https://www.cambridgeinternational.org/assets/img/CAIE_logo_colour.svg" width="40%" height="40%" alt="Cambridge Assessment">
</p>

# Paper Generator

**Status of development:**  
The development of this project has been temperatorily paused, but fear not, after some time I will complete this project and bring this to its ultimate form.

> What is this?

A piece of program that splits question and answers from the PDF provided by CAIE,  
and allow user to filter and merge those questions to get fully printable PDF documents.

> Any demos?

Please look into the demo folder.

Notice that the demos are randomly generated, which meansn you get different contents each time
you run the program.

> How does it work?

1. A scraper scrape PDF from GCEPapers
2. An analyser read the PDF and split question by detecting question numbers.
3. A post_processor generate image and pdf out of those small chunks of PDF.
4. A filter filting the questions, pairing up the qp and ms and tag the questions by keywork.
5. A generator take the filted data and merge them into a complete PDF

It is that simple.

> What subjects does this support?

Pratically all subjects in IG, AS&ALevel. Or even more!

This program is highly configurable, for different subjects, you can add keywords of each chapter  
and it will work, simple as that.

I plan to support CS, Math, Further Math, Chemistry, Physics, and Economics in the future as an example.  
But you can easily create rules for your favourite subject and submit your config to the repo.

> How can I use it?

It's still in development, so relex, and wait for it.

## Quick Start

```bash
python3 -m venv .venv
pip3 install -r requirements.txt

mkdir -p data/pdf
# place your pdf files in pdf folder

python3 src/controller.py
python3 src/categoriser.py
python src/generator.py
```
