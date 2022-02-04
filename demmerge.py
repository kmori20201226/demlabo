import os
import re
import sys
import numpy as np
from osgeo import gdal, ogr
import argparse
import matplotlib.pyplot as plt
from demreader import dem2image

class CommandException(Exception):
    pass

def pick_dems(input_path, pat10, pat5):
    file10 = None
    files5 = {}
    def choose_preferred(p, a, full_b):
        full_a = os.path.join(p, a)
        if full_b is None:
            return full_a
        b = os.path.split(full_b)[1].upper()
        return full_a if a < b else full_b
    for root, dirs, files in os.walk(input_path):
        for file in files:
            mo = re.match(pat5, file.upper())
            if mo is not None:
                lev3 = (int(mo.group(1)), int(mo.group(2)))
                files5[lev3] = choose_preferred(root, file, files5.get(lev3, None))
            else:
                mo = re.match(pat10, file.upper())
                if mo is not None:
                    file10 = choose_preferred(root, file, file10)
    return file10, files5

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mesh", type=str)
    parser.add_argument("--input_path", "-i", default=".", type=str)
    args = parser.parse_args()

    try:
        mo = re.match(r"\d{4}-\d{2}$", args.mesh)
        if mo is None:
            raise CommandException("メッシュは 9999-99 形式で指定する必要がある")
        pat10 = "FG-GML-%s-DEM10." % (mo.group(0),)
        pat5 = "FG-GML-%s-(\d)(\d)-DEM5." % (mo.group(0),)
        file10, files5 = pick_dems(args.input_path, pat10, pat5)
        if file10 is None:
            raise CommandException("%s の DEM10ファイルが見つかりません" % (mo.group(0),))
        print(file10)
        for k, v in files5.items():
            print("  %s: %s" % (k, v))
    except CommandException as ex:
        print(ex)
        sys.exit(1)
    if False:
        plane, meta = dem2image(args.input_file, args.nodata)
        fig = plt.figure()
        plt.imshow(plane)
        fig.canvas.manager.set_window_title(os.path.split(args.input_file)[1])
        plt.show()
