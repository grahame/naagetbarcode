#!/usr/bin/env python3

import os
import sys
import requests
import itertools


def mkdir(d):
    try:
        os.mkdir(d)
    except OSError:
        pass


def grab_jpeg(barcode, tmpd, page):
    fname = "{}/{:08}.jpg".format(tmpd, page)
    if os.access(fname, os.R_OK):
        return fname
    url = "https://recordsearch.naa.gov.au/SearchNRetrieve/NAAMedia/ShowImage.aspx?B={}&T=P&S={}".format(
        barcode, page
    )
    resp = requests.get(url)
    # NAA endpoint doesn't return non-200, it returns a text blurb
    if resp.headers["content-type"].startswith("text/html"):
        return None
    tmpf = fname + ".tmp"
    with open(tmpf, "wb") as fd:
        fd.write(resp.content)
    os.rename(tmpf, fname)
    return fname


def grab_jpegs(barcode):
    parts = []
    tmpd = "tmp/{}".format(barcode)
    mkdir(tmpd)
    for i in itertools.count(1):
        fname = grab_jpeg(barcode, tmpd, i)
        print("{} -> {}".format(i, fname))
        if fname is None:
            break
        parts.append(fname)


def main():
    barcode = sys.argv[1]
    grab_jpegs(barcode)


if __name__ == "__main__":
    main()
