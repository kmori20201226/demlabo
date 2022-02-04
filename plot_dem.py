import os
import numpy as np
from osgeo import gdal, ogr
import argparse
import matplotlib.pyplot as plt
from demreader import dem2image

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("--nodata", "-n", type=int, default=-9999)
    parser.add_argument("--asis", action='store_true', help="Displays nodata value as they are")
    parser.add_argument("--upsample", action='store_true', help="Displays nodata value as they are")
    args = parser.parse_args()
    plane, meta = dem2image(args.input_file, args.nodata)
    if not args.asis:
        plane[plane == np.float32(args.nodata)] = np.nan
    if args.upsample:
        plane = plane.repeat(2, axis=0).repeat(2, axis=1)
    fig = plt.figure()
    plt.imshow(plane)
    fig.canvas.manager.set_window_title(os.path.split(args.input_file)[1])
    plt.show()
