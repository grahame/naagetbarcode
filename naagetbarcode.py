#!/usr/bin/env python3

import os
import sys
import requests
import itertools
import subprocess
import threading
import queue
from multiprocessing import cpu_count


class NAABarcodeAccess:
    @staticmethod
    def mkdir(d):
        try:
            os.mkdir(d)
        except OSError:
            pass

    def __init__(self, working_dir="./tmp/"):
        self._working_dir = working_dir

    def barcode_dir(self, barcode):
        return os.path.join(self._working_dir, barcode)

    def barcode_filename(self, barcode, fname):
        return os.path.join(self.barcode_dir(barcode), fname)

    def grab_jpeg(self, barcode, page):
        fname = self.barcode_filename(barcode, "{:08}.jpg".format(page))
        if os.access(fname, os.R_OK):
            return fname
        url = "https://recordsearch.naa.gov.au/SearchNRetrieve/NAAMedia/ShowImage.aspx?B={}&T=P&S={}".format(
            barcode, page
        )
        print("get page {} -> {}".format(page, fname))
        resp = requests.get(url)
        # NAA endpoint doesn't return non-200, it returns a text blurb
        if resp.headers["content-type"].startswith("text/html"):
            return None
        tmpf = fname + ".tmp"
        with open(tmpf, "wb") as fd:
            fd.write(resp.content)
        os.rename(tmpf, fname)
        return fname

    def grab_jpegs(self, barcode):
        parts = []
        self.mkdir(self.barcode_dir(barcode))
        for i in itertools.count(1):
            fname = self.grab_jpeg(barcode, i)
            if fname is None:
                break
            parts.append(fname)
        return parts

    def ocr_pages(self, barcode, tasks):
        q = queue.Queue()
        # lists are threadsafe in cPython, at least
        results = []

        def worker():
            while True:
                page, jpeg = q.get()
                pfx = self.barcode_filename(barcode, "ocr_{}".format(page))
                pdf = pfx + ".pdf"
                if not os.access(pdf, os.R_OK):
                    subprocess.check_output(["tesseract", "-l", "eng", jpeg, pfx, "pdf"])
                if not os.access(pdf, os.R_OK):
                    raise Exception("tesseract failed: {}".format(pdf))
                results.append((page, pdf))
                q.task_done()

        for i in range(cpu_count()):
            threading.Thread(target=worker, daemon=True).start()

        for task in tasks:
            q.put(task)

        q.join()

        assert(len(results) == len(tasks))
        return [pdf for (page, pdf) in sorted(results)]
        return pdf

    def grab_pdfs(self, barcode):
        """
        not only PDF, but OCRed (with ocrmypdf)
        """
        jpegs = []
        self.mkdir(self.barcode_dir(barcode))
        for page in itertools.count(1):
            jpeg = self.grab_jpeg(barcode, page)
            if jpeg is None:
                break
            jpegs.append((page, jpeg))
        return self.ocr_pages(barcode, jpegs)

    def grab_pdf(self, barcode):
        pdfs = self.grab_pdfs(barcode)
        fname = self.barcode_filename(barcode, "{} ocr.pdf")
        subprocess.check_output(["pdftk"] + pdfs + ["cat", "output", fname])


def main():
    barcode = sys.argv[1]
    access = NAABarcodeAccess()
    access.grab_pdf(barcode)


if __name__ == "__main__":
    main()
