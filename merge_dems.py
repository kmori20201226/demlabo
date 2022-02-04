"""Under construction (作成中)
"""
import os
import re
import sys
import numpy as np
from tqdm import tqdm
from osgeo import gdal, ogr
import argparse
import matplotlib.pyplot as plt
from demreader import dem2image
from demfiles import enum_demfiles
import matplotlib.pyplot as plt

class CommandException(Exception):
    pass

DEBUG2 = False
DEBUG3 = True

def debug_img3(mesh2, dem10, dem5, result):
    fig = plt.figure()
    fig.canvas.manager.set_window_title(mesh2)
    ax1 = fig.add_subplot(1, 3, 1)
    ax1.set_title("DEM10")
    ax1.axis('off')
    ax1.imshow(dem10)
    ax2 = fig.add_subplot(1, 3, 2)
    ax2.set_title("DEM5")
    ax2.axis('off')
    ax2.imshow(dem5)
    ax3 = fig.add_subplot(1, 3, 3)
    ax3.set_title("RESULT")
    ax3.axis('off')
    ax3.imshow(result)
    plt.show()

def debug_img2(mesh2, org, result):
    fig = plt.figure()
    fig.canvas.manager.set_window_title(mesh2)
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.set_title("INPUT")
    ax1.axis('off')
    ax1.imshow(org)
    ax3 = fig.add_subplot(1, 2, 2)
    ax3.set_title("OUTPUT")
    ax3.axis('off')
    ax3.imshow(result)
    plt.show()

DEM5XSIZE = 225
DEM5YSIZE = 150

    
def merge_mesh(mesh2, dem10_path, dem5_files):
    """DEM10 の上に DEM5 をマージする。

    1. DEM10 のデータを縦横２倍にする (DEM5 の間隔に合わせる) 
    2. 10 x 10 の DEM5 イメージ全てを同位置の DEM10の場所で
    3.1  DEM5 から DEM10 へ 欠落値でないものをコピーする
    3.2  コピーされた先の DEM10 の欠落値を 0 で埋める

    Args:
        mesh2 (str): ２次メッシュコード
        dem10_path (dem10img, dem10metaのタプル) : DEM10 ファイル名
        dem5_files (np.array(10x10)): DEM5 ファイル名の配列
    """
    dem10img, dem10meta = dem2image(dem10_path)

    dem10img = dem10img.repeat(2, axis=0).repeat(2, axis=1)
    if DEBUG2: orgimg = dem10img.copy()
    for y in range(10):
        for x in range(10):
            xs = x * DEM5XSIZE
            ys = (9 - y) * DEM5YSIZE
            xe = xs + DEM5XSIZE
            ye = ys + DEM5YSIZE
            cut = dem10img[ys:ye, xs:xe]
            dem5_path = dem5_files[y, x]
            if dem5_path is not None:
                dem5img, dem5meta = dem2image(dem5_path)
                if DEBUG3: cutbak = cut.copy()  # DEBUG
                cut[~np.isnan(dem5img)] = dem5img[~np.isnan(dem5img)]
            cut[np.isnan(cut)] = 0.0
            if DEBUG3:
                debug_img3(mesh2, cutbak, dem5img, cut)
    #dem10img[np.isnan(dem10img)] = 0.0
    if DEBUG2: debug_img2(mesh2, orgimg, dem10img)

def pick_dems(input_path, meshes):
    demtuples = list(enum_demfiles(input_path))
    for mesh2, dem10_path, dem5_array in tqdm(demtuples):
        if not meshes or mesh2 in meshes:
            dem5s = np.full((10, 10), None)
            for y in range(10):
                for x in range(10):
                    dem5_path = dem5_array[y, x]
                    if dem5_path is not None:
                        dem5s[y, x] = dem5_path
            merge_mesh(mesh2, dem10_path, dem5s)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", default=".", type=str)
    parser.add_argument("meshes", nargs='*', type=str)
    args = parser.parse_args()

    try:
        if args.meshes:
            for m in args.meshes:
                mo = re.match(r"\d{4}-\d{2}$", m)
                if mo is None:
                    raise CommandException("メッシュは 9999-99 形式で指定する必要がある")
        pick_dems(args.input_path, args.meshes)
    except CommandException as ex:
        print(ex)
        sys.exit(1)
