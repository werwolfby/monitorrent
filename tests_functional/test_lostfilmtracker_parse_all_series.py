from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import range
from unittest import TestCase
from monitorrent.plugins.trackers.lostfilm import LostFilmTVTracker
from monitorrent.utils.soup import get_soup
import requests
from threading import Thread, Lock
from queue import Queue, Empty


class TestParseAllSeriesTest(TestCase):
    # series with most amount of errors
    failed_series = [24, 30, 40, 51, 65, 66, 112, 125, 172]

    def test_parse_all_series(self):
        error_hrefs = []
        lock = Lock()
        queue = Queue()
        tracker = LostFilmTVTracker()
        threads = []

        def process():
            while True:
                try:
                    url = queue.get(False)
                except Empty:
                    return
                try:
                    tracker.parse_url(url, True)
                except Exception:
                    with lock:
                        error_hrefs.append(url)

        all_series = requests.get('http://www.lostfilm.tv/serials.php')
        soup = get_soup(all_series.text, 'html5')

        mid = soup.find('div', class_='mid')
        series = mid.find_all('a', class_='bb_a')
        for s in series:
            queue.put('http://www.lostfilm.tv' + s.attrs['href'])

        for i in range(0, 20):
            t = Thread(target=process)
            threads.append(t)
            t.start()

        for i in range(0, len(threads)):
            threads[i].join()

        for e in error_hrefs:
            print("Error parse: {0}".format(e))

        self.assertEqual(0, len(error_hrefs))
