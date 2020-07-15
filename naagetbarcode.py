#!/usr/bin/env python3

import os
import sys
import requests
import itertools
import subprocess


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

    def jpeg_to_pdf(self, barcode, page, jpeg):
        pre_ocr = self.barcode_filename(barcode, "tmp_preocr_{}.pdf".format(page))
        post_ocr = self.barcode_filename(barcode, "ocr_{}.pdf".format(page))
        if not os.access(post_ocr, os.R_OK):
            subprocess.check_output(["convert", jpeg, pre_ocr])
            subprocess.check_output(["ocrmypdf", pre_ocr, post_ocr])
            os.unlink(pre_ocr)
        return post_ocr

    def grab_pdfs(self, barcode):
        """
        not only PDF, but OCRed (with ocrmypdf)
        """
        parts = []
        self.mkdir(self.barcode_dir(barcode))
        for i in itertools.count(1):
            jpeg = self.grab_jpeg(barcode, i)
            if jpeg is None:
                break
            pdf = self.jpeg_to_pdf(barcode, i, jpeg)
            parts.append(pdf)
        return parts

    def grab_pdf(self, barcode):
        pdfs = self.grab_pdfs(barcode)
        fname = self.barcode_filename(barcode, "merged_ocr.pdf")
        subprocess.check_output(["pdftk"] + pdfs + ["cat", "output", fname])


def main():
    barcode = sys.argv[1]
    access = NAABarcodeAccess()
    access.grab_pdf(barcode)


if __name__ == "__main__":
    main()
