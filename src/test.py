import requests
import queue
import threading
import logging
import os
from configuration import *
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit,  unquote
from time import sleep

page = requests.get(
    "https://papers.gceguide.com/A%20Levels/Applied%20Information%20and%20Communication%20Technology%20(9713)/")
