import requests
import queue
import threading
import os
import sys
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit,  unquote, quote
from time import sleep
from datasize import DataSize


class GCEScraper:

    def __init__(self, save_path, worker_num=10,
                 worker_delay=0.1, max_size=0, tui=False,
                 attachment_suffix=[".pdf", ".zip"], max_retries=10,
                 file_cnt_limit=0, max_attachment_size=100) -> None:

        self.task_queue = queue.Queue(max_size)
        self.error_queue = queue.Queue(max_size)
        self.state_dict = {i: "" for i in range(0, worker_num)}

        self.tui = tui
        self.save_path = save_path
        self.worker_num = worker_num
        self.worker_delay = worker_delay
        self.attachment_suffix = attachment_suffix
        self.max_retries = max_retries
        self.file_cnt_limit = file_cnt_limit
        self.max_attachment_size = max_attachment_size

        self.terminated = False
        self.download_count = 0

    def add_url(self, url_list):
        [self.task_queue.put([url, self.max_retries]) for url in url_list]

    def run(self):
        def update_state_func(i):
            def _update_state(text):
                if self.tui:
                    self.state_dict[i] = text
                else:
                    print("worker " + str(i) + " : " + text)

            return _update_state

        # create workers
        self.workers = [threading.Thread(target=self._worker, args=(
            self.worker_delay, update_state_func(i))) for i in range(0, self.worker_num)]

        # start workers
        [worker.start() for worker in self.workers]

        # start other superviours
        self.supervisor = threading.Thread(
            target=self._supervisor)
        self.supervisor.start()

        # end
        self.task_queue.join()
        self.terminated = True

        error_list = []
        while not self.error_queue.empty():
            error_list.append(self.error_queue.get())
        return error_list

    def _supervisor(self):
        if self.tui:
            sys.stdout.write("\n" * (self.worker_num + 1))
        while threading.active_count() > 2:
            # supervisor, main + workers
            sleep(0.1)
            # count
            if self.file_cnt_limit != 0:
                if self.download_count > self.file_cnt_limit:
                    self.terminated = True

            # printing
            if self.tui:

                for i in range(0, self.worker_num + 1):
                    sys.stdout.write("\x1b[1A\x1b[2K")

                sys.stdout.write("count: \t" +
                                 str(threading.active_count()-2) + "\n")

                for key in self.state_dict:
                    sys.stdout.write("worker" + str(key) + ":\t" +
                                     self.state_dict[key] + "\n")

        while self.task_queue.unfinished_tasks > 0:
            self.task_queue.task_done()

    def _html_url_handler(self, abs_url) -> list:
        if not abs_url.endswith("/"):
            abs_url += "/"
        page = requests.get(abs_url)
        soup = BeautifulSoup(page.content, "html.parser")
        results = []
        paper_list = soup.find(id="paperslist")
        if paper_list is not None:
            for li in paper_list.find_all("li"):
                results.append(
                    urljoin(abs_url, li.find("a").get("href")))
        else:
            self.error_queue.put(abs_url)

        return results

    @staticmethod
    def pathgen(save_path, abs_url):
        sub_path = "-".join(list(filter(("").__ne__, unquote(
            urlsplit(abs_url).path[1:]).strip().replace(" ", "-").split("-"))))
        return os.path.join(save_path, sub_path)

    def _attachment_url_handler(self, abs_url):
        path = GCEScraper.pathgen(self.save_path, abs_url)

        if os.path.exists(path):
            return

        # not exist, download the file
        file = requests.get(abs_url).content
        if sys.getsizeof(file) >= self.max_attachment_size:
            self.error_queue.put(abs_url)
            return

        # check if file size exceeds max size

        # save the file
        dirpath = os.path.split(path)[0]
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(path, "wb") as file_on_disk:
            file_on_disk.write(file)

        # update download count
        self.download_count += 1

    def _worker(self,  delay, update_state):
        while not self.terminated:
            sleep(delay)
            if self.task_queue.empty():
                sleep(1)
                continue

            task = self.task_queue.get()
            if task[1] == 0:
                self.error_queue.put(task[0])
                update_state("GIVEUP " + task[0])
                continue
            else:
                task[1] -= 1

            update_state("GET " + task[0])

            try:
                is_attachment = False
                for suffix in self.attachment_suffix:
                    if task[0].endswith(suffix):
                        is_attachment = True

                if is_attachment:
                    self._attachment_url_handler(task[0])
                else:
                    new_urls = self._html_url_handler(task[0])
                    self.add_url(new_urls)
            except Exception as e:
                self.task_queue.put(task)
                update_state("RETRY " + task[0])

            self.task_queue.task_done()

        update_state("TERMINATED")


def main():

    parser = argparse.ArgumentParser(description="gcepaper web scraper")
    parser.add_argument("save_location", metavar="path",
                        type=str, help="parent dir to save the scraped files.", default="/")
    parser.add_argument(
        "--thread", type=int, help="number of parallel workers", metavar="int", default=50)
    parser.add_argument(
        "--delay", type=float, help="delay after each request", metavar="float",  default=0)
    parser.add_argument("-r", "--retries", type=int,
                        help="maximum retries after giving up a url", metavar="int", default=10)
    parser.add_argument(
        "--tui", help="friendly user interface", action="store_true")
    parser.add_argument(
        "--limit", "file-cnt-limit", dest="file_cnt_limit",   help="limit how many files can download", type=int, metavar="int",  default=0)
    parser.add_argument(
        "--max-attachment-size", dest="max_attchment_size",   help="the file larger than this size won't be downloaded, e.g. 100MiB ", type=int, metavar="int",  default=0)
    parser.add_argument("--suffix", dest="attachment_suffix", type=str,
                        help="url with given suffix will be downloaded", metavar="suffix", nargs="+", default=[".pdf"])
    parser.add_argument("--baseurl", type=str,
                        help="the parent url which starts downloading", metavar="url",  default="https://papers.gceguide.com/")

    args = parser.parse_args()

    max_attchment_size = DataSize(args.max_attachment_size).__format__("1B")

    gce_scraper = GCEScraper(
        args.save_location, worker_num=args.thread, worker_delay=args.delay, tui=args.tui, attachment_suffix=args.attachment_suffix, file_cnt_limit=args.file_cnt_limit, max_attachment_size=max_attchment_size)
    gce_scraper.add_url([args.baseurl])

    error_list = gce_scraper.run()

    with open(os.path.join(GCEScraper.pathgen(args.save_location, args.baseurl) + "/scraper_errors.txt"), "w") as debugfile:
        debugfile.write("\n".join(error_list))


if __name__ == "__main__":
    exit(main())
