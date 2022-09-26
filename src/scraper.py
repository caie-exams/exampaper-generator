import requests
import queue
import threading
import os
import sys
from configuration import *
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit,  unquote, quote
from time import sleep


class GCEScraper:

    def __init__(self, save_path, worker_num=10, worker_delay=0.1, max_size=0, tui=False) -> None:
        self.BASE_URL = "https://papers.gceguide.com/"
        self.task_queue = queue.Queue(max_size)
        self.error_queue = queue.Queue(max_size)
        self.state_dict = {i: "" for i in range(0, worker_num)}

        self.tui = tui
        self.save_path = save_path
        self.worker_num = worker_num

        self.terminated = False
        self.task_queue.put(self.BASE_URL)
        self.task_queue.put(
            "https://papers.gceguide.com/A%20Levels/9707_s14_ms_22.pdf")

        def update_state_func(i):
            def _update_state(text):
                self.state_dict[i] = text
            return _update_state

        # create workers
        self.workers = [threading.Thread(target=self._worker, args=(
            "worker-" + str(i), worker_delay, update_state_func(i))) for i in range(0, worker_num)]

    def run(self):
        # start workers
        [worker.start() for worker in self.workers]

        if self.tui:
            self.live_display_worker = threading.Thread(
                target=self._live_display)
            self.live_display_worker.start()

        # end
        self.task_queue.join()
        self.terminated = True

        return list(self.error_queue)

    def _live_display(self):
        if self.tui:
            sys.stdout.write("\n" * self.worker_num)
        while not self.terminated:
            sleep(0.1)
            # if tui, rewrite multiple lines
            if self.tui:
                for i in range(0, self.worker_num):
                    sys.stdout.write("\x1b[1A\x1b[2K")

            for key in self.state_dict:
                sys.stdout.write("worker" + str(key) + ":\t" +
                                 self.state_dict[key] + "\n")

    def _html_url_handler(self, abs_url) -> list:
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

    def _pdf_url_handler(self, abs_url) -> bool:
        path = os.path.join(self.save_path, unquote(
            urlsplit(abs_url).path[1:]))

        if os.path.exists(path):
            return False

        # not exist, download the file
        file = requests.get(abs_url).content

        # save the file
        dirpath = os.path.split(path)[0]
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(path, "wb") as file_on_disk:
            file_on_disk.write(file)

    def _worker(self, worker_name, delay, update_state):
        while not self.terminated:
            sleep(delay)
            if self.task_queue.empty():
                sleep(1)
                continue
            task = self.task_queue.get()
            update_state("GET " + task)

            if task.endswith(".pdf"):
                try:
                    self._pdf_url_handler(task)
                except:
                    self.error_queue.put(task)
            else:
                try:
                    new_tasks = self._html_url_handler(task)
                    [self.task_queue.put(new_task) for new_task in new_tasks]
                except:
                    self.error_queue.put(task)
            self.task_queue.task_done()

        print(worker_name + " terminated")


def main():
    gce_scraper = GCEScraper(DEBUG_DIR_PATH + "scraped_pdf/", 20, tui=1)
    errors_list = gce_scraper.run()
    print(errors_list)
    with open(DEBUG_DIR_PATH + "scraper_errors.json", "w") as debugfile:
        debugfile.write("\n".join(list))


if __name__ == "__main__":
    exit(main())
