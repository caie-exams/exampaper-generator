from constants import *
from processor_model import *

import PyPDF2
from fuzzysearch import find_near_matches
from func_timeout import func_timeout, FunctionTimedOut
import time

# job:
# clean the text to make it ready for search


class Analyser(ProcessorModel):

    """
    clean the text in question to make it ready for search
    by fuzzy search in text extracted from original pdf

    input - individual quesitons  
    output - processed individual quesitons  

    realation is one-to-one 
    """

    @ staticmethod
    def __extract_text_from_pdf(pdfname, page):
        pdfpath = DATA_DIR_PATH + "pdf/" + pdfname + ".pdf"
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

    def _process(self, question):

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

        return [question]


TEST_DATA = [{'pdfname': '0620_s20_qp_11', 'question_num': 1, 'location': [{'page_num': 1, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 676}], 'text': 'Nitrogen is heated in a balloon, which expands slightly.  Which statements about the molecules of nitrogen are correct?  1 They move further apart.  2 They move more quickly.  3 They remain the same distance apart.  4 Their speed remains unchanged.    A 1and2 B 1and4 C 2and3 D 3and4 '}, {'pdfname': '0620_s20_qp_11', 'question_num': 2, 'location': [{'page_num': 1, 'left': 175, 'right': 1550, 'top': 676, 'bottom': 1027}], 'text': 'Which piece of apparatus should be used to measure exactly 21.4. of water?  A 25cm? beaker  B 25cm’ pipette  C 50cm* burette  D    50cm* measuring cylinder '}, {'pdfname': '0620_s20_qp_11', 'question_num': 3, 'location': [{'page_num': 1, 'left': 175, 'right': 1550, 'top': 1027, 'bottom': 1379}], 'text': 'Which method of separation is used to separate a soluble solid from its solution?  A chromatography  B_ condensation  C_crystallisation  D    filtration '}, {'pdfname': '0620_s20_qp_11', 'question_num': 4, 'location': [{'page_num': 1, 'left': 175, 'right': 1550, 'top': 1379, 'bottom': 2026}], 'text': 'The atomic number and nucleon number of a potassium atom are shown.         potassium atom         atomic number 19              nucleon number 39         How many protons, neutrons and electrons are in a potassium ion, K*?              protons neutrons electrons  A 19 20 18  B 19 20 20  Cc 20 19 18  D 20 19 19                               '}, {'pdfname': '0620_s20_qp_11', 'question_num': 5, 'location': [{'page_num': 2, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 741}], 'text': 'Sodium is in Group of the Periodic Table.    Chlorine is in Group VII of the Periodic Table.    Sodium and chlorine combine to form a compound.    Which statement about the combination of sodium and chlorine atoms is correct?    A    B  Cc  D    Both sodium and chlorine lose electrons.  Both sodium and chlorine gain electrons.  Sodium loses electrons and chlorine gains electrons.    Sodium gains electrons and chlorine loses electrons. '}, {'pdfname': '0620_s20_qp_11', 'question_num': 6, 'location': [{'page_num': 2, 'left': 175, 'right': 1550, 'top': 741, 'bottom': 1543}], 'text': 'The electronic structures of two atoms, P and Q, are shown.    P and Q combine together to form a compound.    What is the type of bonding in the compound and what is the formula of the compound?                                     type of bonding formula  A ionic PQ  B ionic PQ,  Cc covalent PQ,  D covalent PQ '}, {'pdfname': '0620_s20_qp_11', 'question_num': 7, 'location': [{'page_num': 3, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 945}], 'text': 'The structures of diamond and graphite are shown.    Which statement about diamond and graphite is correct?    A    B  Cc  D    Diamond and graphite have low melting points.    Diamond and graphite have mobile electrons.    Diamond and graphite have layered structures.    Diamond and graphite contain strong covalent bonds between carbon atoms. '}, {'pdfname': '0620_s20_qp_11', 'question_num': 8, 'location': [{'page_num': 3, 'left': 175, 'right': 1550, 'top': 945, 'bottom': 1367}], 'text': 'Aluminium oxide has the formula Al2O3.    Which statement about aluminium oxide is correct?    A    B  Cc  D    2g of aluminium atoms are combined with 3g of oxygen atoms.    2g of aluminium atoms are combined with 3g of oxygen molecules.    Aluminium oxide has a relative formula mass of 102.    Pure aluminium oxide contains a higher mass of oxygen than of aluminium. '}, {'pdfname': '0620_s20_qp_11', 'question_num': 9, 'location': [{'page_num': 3, 'left': 175, 'right': 1550, 'top': 1367, 'bottom': 1800}], 'text': 'Which products are formed when dilute sulfuric acid undergoes electrolysis?         at the anode    at the cathode              500 BW >    oxygen  hydrogen  sulfur dioxide    oxygen              hydrogen  oxygen  hydrogen    sulfur dioxide           '}, {'pdfname': '0620_s20_qp_11', 'question_num': 10, 'location': [{'page_num': 3, 'left': 175, 'right': 1550, 'top': 1800, 'bottom': 2068}], 'text': 'Which element is not used as a fuel?    >    carbon  helium  hydrogen    uranium '}, {'pdfname': '0620_s20_qp_11', 'question_num': 11, 'location': [{'page_num': 4, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 1199}], 'text': 'The energy level diagram shows the energy of the reactants and products in a chemical reaction.    reactants  energy    products         progress of reaction    Which row correctly describes the energy change and the type of reaction shown?         description of    energy change type of reaction         A energy is given out endothermic  to the surroundings    B energy is given out exothermic  to the surroundings    C | energy is taken in from endothermic  the surroundings    D | energy is taken in from exothermic  the surroundings                          '}, {'pdfname': '0620_s20_qp_11', 'question_num': 12, 'location': [{'page_num': 4, 'left': 175, 'right': 1550, 'top': 1199, 'bottom': 1705}], 'text': 'Which diagram represents a chemical change?    A B    oo 33. F %    Oo Ce  Cc D  Ge  os —-° O o3 ee  ee ee id e '}, {'pdfname': '0620_s20_qp_11', 'question_num': 13, 'location': [{'page_num': 5, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 1305}], 'text': 'The rate of reaction between magnesium and hydrochloric acid is investigated.    The volume of hydrogen given off at different times is measured.  The results are shown.    25                                  20                                  volume of 15                                                                                                                                                                                                                                                                                                                                    hydrogen   /cm? 10  5  0    0 10 20 30 40 50 60 70 80 90  time/s    Which conclusions are correct?    1 The rate is fastest between 0 and 20 seconds.  2 The maximum volume of hydrogen given off is 22cm’.    3 At40 seconds, 20cm’ of hydrogen is given off.    A tand2only B t1and3only C 2and3o0nly D 1,2and3    100 '}, {'pdfname': '0620_s20_qp_11', 'question_num': 14, 'location': [{'page_num': 5, 'left': 175, 'right': 1550, 'top': 1305, 'bottom': 1660}], 'text': 'Which reaction can be easily reversed?  A dissolving zinc in hydrochloric acid  B_ fermenting glucose with yeast  C_ heating hydrated cobalt(II) chloride  D    the rusting of an iron nail '}, {'pdfname': '0620_s20_qp_11', 'question_num': 15, 'location': [{'page_num': 5, 'left': 175, 'right': 1550, 'top': 1660, 'bottom': 2005}], 'text': 'Carbon reacts with silver oxide to form carbon dioxide and silver.    Which substance is reduced?    A carbon   B_ carbon dioxide  C silver   D - silver oxide '}, {'pdfname': '0620_s20_qp_11', 'question_num': 16, 'location': [{'page_num': 6, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 882}], 'text': 'The graph shows how the pH of a solution changes as an acid is added to an alkali.    acid + alkali — salt + water    Which letter represents the area of the graph where both acid and salt are present?         volume of acid added '}, {'pdfname': '0620_s20_qp_11', 'question_num': 17, 'location': [{'page_num': 6, 'left': 175, 'right': 1550, 'top': 882, 'bottom': 1420}], 'text': 'Phosphorus is an element in Group of the Periodic Table.    It burns in air to form an oxide, which dissolves in water to form a solution with a pH of 1.    Which row describes this oxide of phosphorus?                                               metal non-metal acidic basic  oxide oxide oxide oxide  A v x v x  B v x x v  Cc x v v x  D x v x v '}, {'pdfname': '0620_s20_qp_11', 'question_num': 18, 'location': [{'page_num': 7, 'left': 175, 'right': 1550, 'top': 181, 'bottom': 1143}], 'text': 'The apparatus shown is used to prepare aqueous copper(II) sulfate.    filter paper    stirrer  excess of solid X  solid X    Y Se aqueous  copper(II) sulfate  heat    What are X and Y?                                  Xx Y  A copper aqueous iron(II) sulfate  B copper(II) chloride dilute sulfuric acid  Cc copper(II) oxide dilute sulfuric acid  D sulfur aqueous copper(II) chloride      '}, {'pdfname': '0620_s20_qp_11', 'question_num': 19, 'location': [{'page_num': 7, 'left': 175, 'right': 1550, 'top': 1143, 'bottom': 1657}], 'text': 'Two tests are carried out on substance Z.    test1 A flame test produces a red flame.    test2 Z is dissolved in water and dilute nitric acid is added, followed by    aqueous silver nitrate. A yellow precipitate is produced.  What is substance Z?  A lithium bromide  B lithium iodide  C sodium bromide  D    sodium iodide '}, {'pdfname': '0620_s20_qp_11', 'question_num': 20, 'location': [{'page_num': 8, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 734}], 'text': 'The elements in Period 3 of the Periodic Table are shown.         Na | Mg} Al | Si P iS) Cl | Ar                                                      Which statements about the elements in Period 3 are correct?    1 Na, Mg and Alare metals.  2. §S, Cland Ar are non-metals.    3. Si, P and S are metals.    A 1and2only B t1and3only C 2and3o0nly D 1,2and3 '}, {'pdfname': '0620_s20_qp_11', 'question_num': 21, 'location': [{'page_num': 8, 'left': 175, 'right': 1550, 'top': 734, 'bottom': 1226}], 'text': 'A Group! metal (lithium, sodium or potassium) is reacted with a Group VII element (chlorine,  bromine or iodine).    Which compound is formed when the Group | metal of highest density reacts with the Group VII  element of lowest density?    A lithium chloride   B_ potassium chloride  C_ potassium iodide  D    lithium iodide '}, {
    'pdfname': '0620_s20_qp_11', 'question_num': 22, 'location': [{'page_num': 8, 'left': 175, 'right': 1550, 'top': 1226, 'bottom': 1694}], 'text': 'The properties of the element titanium, Ti, can be predicted from its position in the Periodic Table.    Which row identifies the properties of titanium?                   can be used conducts electricity . forms coloured  , has low density  as a catalyst when solid compounds  A v Jv v x  B v Jv x v  Cc v x v v  D x Jv v v                               '}, {'pdfname': '0620_s20_qp_11', 'question_num': 23, 'location': [{'page_num': 9, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 753}], 'text': 'balloon is filled with helium. Helium is a noble gas and makes the balloon rise up in the air.  The density of air is 1.23 g/dm*.    Which gas is helium?                                  density in g/dm? reaction with oxygen  A 0.0899 burns rapidly  B 0.179 does not react with oxygen  Cc 1.78 does not react with oxygen  D 3.75 does not react with oxygen      '}, {'pdfname': '0620_s20_qp_11', 'question_num': 24, 'location': [{'page_num': 9, 'left': 175, 'right': 1550, 'top': 753, 'bottom': 1104}], 'text': 'Which property is shown by all metals?  A They are extracted from their ores by heating with carbon.  B_ They conduct electricity.  C_ They form acidic oxides.  D    They react with hydrochloric acid to form hydrogen. '}, {'pdfname': '0620_s20_qp_11', 'question_num': 25, 'location': [{'page_num': 9, 'left': 175, 'right': 1550, 'top': 1104, 'bottom': 1839}], 'text': 'The properties of four metals, W, X, Y and Z, are shown.  W_ It does not react with cold water but reacts with steam.  X_ It does not react with water or dilute acid but the oxide of X is reduced by carbon.  Y The oxide of Y is not reduced by carbon but Y reacts vigorously with cold water.  Z__ It does not react with water or steam but reacts with dilute acid.    What is the order of reactivity of the elements starting with the most reactive?              most least  reactive reactive  A Xx Ww Z Y  B Xx Z Ww Y  Cc Y Ww Z Xx  D Y Z Ww Xx                                    '}, {'pdfname': '0620_s20_qp_11', 'question_num': 26, 'location': [{'page_num': 10, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 788}], 'text': 'Molten iron from the blast furnace contains impurities.    The process of turning the impure iron into steel involves blowing oxygen into the molten iron and  adding calcium oxide.    What are the reasons for blowing in oxygen and adding calcium oxide?         blowing in oxygen    adding calcium oxide              500 W >    carbon is removed by reacting with oxygen  carbon is removed by reacting with oxygen    iron reacts with the oxygen         iron reacts with the oxygen         reacts with acidic impurities making slag  reacts with slag and so removes it  reacts with acidic impurities making slag    reacts with slag and so removes it           '}, {'pdfname': '0620_s20_qp_11', 'question_num': 27, 'location': [{'page_num': 10, 'left': 175, 'right': 1550, 'top': 788, 'bottom': 1221}], 'text': 'Which row describes two uses of the named steel?                   type of steel uses  A mild steel cutlery and car bodies  B mild steel car bodies and chemical plant  Cc stainless steel cutlery and chemical plant  D stainless steel car bodies and cutlery           '}, {'pdfname': '0620_s20_qp_11', 'question_num': 28, 'location': [{'page_num': 10, 'left': 175, 'right': 1550, 'top': 1221, 'bottom': 1581}], 'text': 'Which statement shows that liquid is pure water?    A    B  Cc  D    It boils at 100°C.  It has a pH value of 7.  It turns blue cobalt(II) chloride pink.    It turns white copper(II) sulfate blue. '}, {'pdfname': '0620_s20_qp_11', 'question_num': 29, 'location': [{'page_num': 10, 'left': 175, 'right': 1550, 'top': 1581, 'bottom': 2048}], 'text': 'Some gases are present in clean air while other gases are only present in polluted air.    Which row is correct?                                     a gas present a gas only present  in clean air in polluted air  A argon carbon dioxide  B argon nitrogen dioxide  Cc sulfur dioxide carbon dioxide  D sulfur dioxide nitrogen dioxide '}, {'pdfname': '0620_s20_qp_11', 'question_num': 30, 'location': [{'page_num': 11, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 1031}], 'text': 'The diagrams show experiments to investigate rusting of iron nails.       1 2 3  ia  layer  of oil  tap salt boiled  water water water  In which test-tubes do the nails rust?  A 1only B 1and2only C t1and3only D 1,2and3 '}, {'pdfname': '0620_s20_qp_11', 'question_num': 31, 'location': [{'page_num': 11, 'left': 175, 'right': 1550, 'top': 1031, 'bottom': 1382}], 'text': 'Which mixture contains all of the elements in a typical fertiliser?  A ammonium nitrate and calcium phosphate  B ammonium phosphate and potassium chloride  C potassium nitrate and ammonium chloride  D_ potassium carbonate and ammonium nitrate '}, {'pdfname': '0620_s20_qp_11', 'question_num': 32, 'location': [{'page_num': 11, 'left': 175, 'right': 1550, 'top': 1382, 'bottom': 1725}], 'text': 'Which processes produce methane?  1 complete combustion of carbon-containing compounds  2 decomposition of vegetation  3. digestion in animals  4 respiration in animals  A 1and4 B 1and3 C 2and3 D 2and4 '}, {'pdfname': '0620_s20_qp_11', 'question_num': 33, 'location': [{'page_num': 12, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 671}], 'text': 'The list shows four methods that were suggested for the formation of carbon dioxide.    Which methods would result in the production of carbon dioxide?    A 1and2    1    2  3  4    cracking methane using steam    action of heat on a carbonate    complete combustion of methane    reaction of a carbonate with oxygen    1 and 4    C 2and3 '}, {'pdfname': '0620_s20_qp_11', 'question_num': 34, 'location': [{'page_num': 12, 'left': 175, 'right': 1550, 'top': 671, 'bottom': 1103}], 'text': 'A student suggests three uses of calcium carbonate (limestone).    1  2  3    manufacture of cement    manufacture of iron    treating alkaline soils    Which suggestions are correct?    A tand2only B    1 and 3 only    C 2and3 only '}, {'pdfname': '0620_s20_qp_11', 'question_num': 35, 'location': [{'page_num': 12, 'left': 175, 'right': 1550, 'top': 1103, 'bottom': 1499}], 'text': 'Which list shows the fractions obtained from distilling petroleum, in order of increasing boiling    point?    A bitumen > diesel oil — fuel oil > lubricating oil    diesel oil         > gasoline    > naphtha — kerosene    B  C_ gasoline + naphtha > kerosene — diesel oil  D    kerosene — lubricating oil + naphtha —> refinery gas '}, {'pdfname': '0620_s20_qp_11', 'question_num': 36, 'location': [{'page_num': 12, 'left': 175, 'right': 1550, 'top': 1499, 'bottom': 1773}], 'text': 'Which statement about members of a homologous series is correct?  A_ They are elements with the same chemical properties.  They are compounds with the same functional group.    B  C_ They are atoms with the same number of outer electrons.  D    They are molecules with the same boiling point. '}, {'pdfname': '0620_s20_qp_11', 'question_num': 37, 'location': [{'page_num': 13, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 757}], 'text': '   Increasing the number of atoms in one    energy released when it burns.    What is the correct order?    molecule of a hydrocarbon increases the amount of                                  less energy more energy  released released  A ethene ethane methane  B ethene methane ethane  Cc methane ethane ethene  D methane ethene ethane           '}, {'pdfname': '0620_s20_qp_11', 'question_num': 38, 'location': [{'page_num': 13, 'left': 175, 'right': 1550, 'top': 757, 'bottom': 1185}], 'text': 'Which statements about ethanol are correct?    1 Ethanol is made by reacting steam with ethene at 300°C.  2 Ethanol is made by fermentation at 55°C.   3 Ethanol burns to produce carbon dioxide and water.   4 Ethanol contains a carbon-carbon double bond.    A 1and2 B 1and3 C 2and3 D 3and4 '}, {'pdfname': '0620_s20_qp_11', 'question_num': 39, 'location': [{'page_num': 13, 'left': 175, 'right': 1550, 'top': 1185, 'bottom': 1780}], 'text': 'Some properties of an organic compound are listed.  e = It is a liquid at room temperature.  e It is soluble in water.  e A solution of J reacts with calcium carbonate to form carbon dioxide.    e Asolution of J has a pH of 3.    In which homologous series does J belong?    A_ alkane  B_ alkene  C_ alcohol  D_ carboxylic acid '}, {'pdfname': '0620_s20_qp_11', 'question_num': 40, 'location': [{'page_num': 14, 'left': 175, 'right': 1550, 'top': 179, 'bottom': 2190}], 'text': 'Which polymers or types of polymer are synthetic?    1 carbohydrates  2 nylon   3. proteins  4 Terylene    A 1and3 B iand4 C 2and3 D 2and4 to reproduce items where third-party owned material protected by copyright is included has been sought and cleared where possible. Every effort has been made by the publisher (UCLES) to trace copyright holders, but if any items requiring clearance have unwittingly been included, the will be pleased to make amends at the earliest possible opportunity. the issue of disclosure of answer-related information to candidates, all copyright acknowledgements are reproduced online in the Cambridge International Education Copyright Acknowledgements Booklet. This is produced for each series of examinations and is freely available to download after the live examination series. Assessment International Education is part of the Cambridge Assessment Group. Cambridge Assessment is the brand name of the University of Local Examinations Syndicate (UCLES), which itself is a department of the University of Cambridge. '}]


def main():
    done_data = []

    post_processor = Analyser(done_data)
    post_processor.start()
    print(post_processor.status())
    for question in TEST_DATA:
        post_processor.add_task(question)
    isrunning = True
    post_processor.stop()
    while isrunning:
        isalive, isrunning, leng = post_processor.status()
        print(isalive, isrunning, leng)
        time.sleep(1)

    print(done_data)


if __name__ == "__main__":
    exit(main())
