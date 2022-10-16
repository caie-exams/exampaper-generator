import re


class Filter:

    """
    provides various methods to filter the question data
    """

    # pdf name

    @staticmethod
    def pdfname_matching(pattern: str, data_list: list):
        for data in data_list:
            if re.match(pattern, data["pdfname"]):
                yield data

    @staticmethod
    def get_ms(data_list: list):
        return Filter.pdfname_matching(".*_ms_.*", data_list)

    @staticmethod
    def get_qp(data_list: list):
        return Filter.pdfname_matching(".*_qp_.*", data_list)

    # pdf type

    @staticmethod
    def get_ms_mcq(data_list: list):
        for data in data_list:
            if data["text"] in ["A", "B", "C", "D"]:
                yield data

    # pdf text

    @staticmethod
    def include_text(text: str, data_list: list):
        for data in data_list:
            if text in data["text"]:
                yield data

    @staticmethod
    def exclude_text(text: str, data_list: list):
        for data in data_list:
            if text not in data["text"]:
                yield data

    @staticmethod
    def include_any_text(text_list: list, data_list: list):
        for data in data_list:
            for text in text_list:
                if text in data["text"]:
                    yield data
                    break

    @staticmethod
    def include_all_text(text_list: list, data_list: list):
        for data in data_list:
            flag = True
            for text in text_list:
                if text not in data["text"]:
                    flag = False
                    break

            if flag:
                yield data

    @staticmethod
    def exclude_any_text(text_list: list, data_list: list):
        for data in data_list:
            for text in text_list:
                if text not in data["text"]:
                    yield data
                    break

    @staticmethod
    def exclude_all_text(text_list: list, data_list: list):
        for data in data_list:
            flag = True
            for text in text_list:
                if text in data["text"]:
                    flag = False
                    break

            if flag:
                yield data
