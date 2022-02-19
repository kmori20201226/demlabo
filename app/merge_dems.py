"""DEMデータをメッシュ毎にマージする

DEMデータには5m間隔のものと10m間隔のものがある。5m間隔のものの
特徴として河川等の標高の値が欠落している。その欠落した箇所のデータを
10m間隔のものから補完する。10m間隔のものも海域はデータが欠落している
ため、標高を0m とする。

Usage :-

  python merge_dems.py [options] <input-path> [mesh...]

  options:
    -o <output-path> 
    --dem10  ... 出力単位を２次メッシュとする
    --dem5   ... 出力単位を３次メッシュとする
"""
import os
import re
import sys
import numpy as np
from osgeo import gdal, ogr
import argparse
import matplotlib.pyplot as plt
from demreader import dem2image
from demfiles import enum_demfiles
from geotiff import write_geotiff
from datetime import datetime

VERSION = "1.00"
class CommandException(Exception):
    pass

def debug_img3(mesh2, dem10, dem5, result):
    import matplotlib.pyplot as plt
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
    import matplotlib.pyplot as plt
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

class MergeOptions:
    def __init__(self):
        self.debug10 = False
        self.debug5 = False
        self.output_dir = None
        self.output10 = False
        self.output5 = False
        self.read10_count = 0
        self.read5_count = 0
        self.output10_count = 0
        self.output5_count = 0

def merge_mesh(mesh2, dem10_path, dem5_files, opt:MergeOptions):
    """DEM10 の上に DEM5 をマージする。

    1. DEM10 のデータを縦横２倍にする (DEM5 の間隔に合わせる) 
    2. 10 x 10 の DEM5 イメージ全てを同位置の DEM10の場所で
    3.1  DEM5 から DEM10 へ 欠落値でないものをコピーする
    3.2  コピーされた先の DEM10 の欠落値を 0 で埋める
    3.3  debug_dem5 が ON であれば３次メッシュの処理結果を表示する
    3.4  output_dem5 が ON であれば３次メッシュの処理結果を出力する
    4. debug_dem10 が ON であれば２次メッシュの処理結果を表示する
    5. output_dem10 が ON であれば２次メッシュの処理結果を出力する

    Args:
        mesh2 (str): ２次メッシュコード
        dem10_path (dem10img, dem10metaのタプル) : DEM10 ファイル名
        dem5_files (np.array(10x10)): DEM5 ファイル名の配列
        opt (MergeOptions): オプション
    """
    def output_path(mesh2, mesh3=None):
        if mesh3 is not None:
            os.makedirs(os.path.join(opt.output_dir, mesh2), exist_ok=True)
            return os.path.join(opt.output_dir,
                    mesh2,
                    "FG-GML-%s-%s.tiff" % (mesh2, mesh3)
                    )
        else:
            os.makedirs(opt.output_dir, exist_ok=True)
            return os.path.join(opt.output_dir,
                    "FG-GML-%s.tiff" % (mesh2,))

    print(dem10_path, flush=True)
    dem10img, dem10meta = dem2image(dem10_path)
    opt.read10_count += 1
    dem10img = dem10img.repeat(2, axis=0).repeat(2, axis=1)
    if opt.debug10: orgimg = dem10img.copy()
    for y in range(9,-1,-1):
        rowprogress = []
        for x in range(10):
            xs = x * DEM5XSIZE
            ys = (9 - y) * DEM5YSIZE
            xe = xs + DEM5XSIZE
            ye = ys + DEM5YSIZE
            cut = dem10img[ys:ye, xs:xe]
            dem5_path = dem5_files[y, x]
            if dem5_path is not None:
                dem5img, dem5meta = dem2image(dem5_path)
                opt.read5_count += 1
                if opt.debug5: cutbak = cut.copy()  # DEBUG
                cut[~np.isnan(dem5img)] = dem5img[~np.isnan(dem5img)]
                rowprogress += ["■"]
            else:
                rowprogress += ["□"]
            cut[np.isnan(cut)] = 0.0
            if opt.debug5:
                debug_img3(mesh2, cutbak, dem5img, cut)
            if opt.output5:
                write_geotiff(output_path(mesh2, "%d%d" % (y, x)), dem5img, dem5meta)
                opt.output5_count += 1
        print("  " + ("".join(rowprogress)), flush=True)
    #dem10img[np.isnan(dem10img)] = 0.0
    if opt.debug10:
        debug_img2(mesh2, orgimg, dem10img)
    if opt.output10:
        write_geotiff(output_path(mesh2), dem10img, dem10meta)
        opt.output10_count += 1

def pick_dems(input_path, meshes, opt:MergeOptions):
    demtuples = list(enum_demfiles(input_path))
    for mesh2, dem10_path, dem5_array in demtuples:
        if not meshes or mesh2 in meshes:
            dem5s = np.full((10, 10), None)
            for y in range(10):
                for x in range(10):
                    dem5_path = dem5_array[y, x]
                    if dem5_path is not None:
                        dem5s[y, x] = dem5_path
            merge_mesh(mesh2, dem10_path, dem5s, opt)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", default=".", type=str)
    parser.add_argument("meshes", nargs='*', type=str)
    parser.add_argument("--output", "-o", default=".", help="Output directory of generated geotiff files")
    parser.add_argument("--dem10", "--output-mesh2", action="store_true", help="Output geotiff (size=2nd mesh)")
    parser.add_argument("--dem5", "--output-mesh3", action="store_true", help="Output geotiff (size=3rd mesh)")
    parser.add_argument("--debug_dem10", action="store_true", help="Debug image (size=2nd mesh)")
    parser.add_argument("--debug_dem5", action="store_true", help="Debug image (size=3rd mesh)")
    args = parser.parse_args()
    opt = MergeOptions()
    opt.output_dir = args.output
    try:
        demcmd = os.environ['DEMCMD']
        opt.output10 = opt.output5 = False
        for cmd in demcmd.split(','):
            if cmd == '--dem10': opt.output10 = True
            if cmd == '--dem5': opt.output5 = True
    except KeyError:
        opt.output10 = args.dem10
        opt.output5 = args.dem5
    st = datetime.now()
    try:
        if args.meshes:
            for m in args.meshes:
                mo = re.match(r"\d{4}-\d{2}$", m)
                if mo is None:
                    raise CommandException("メッシュは 9999-99 形式で指定する必要がある")
        print("%s %s" % (sys.argv[0], VERSION), flush=True)
        pick_dems(args.input_path, args.meshes, opt)
        print("2次メッシュDEMファイル数: %d" % (opt.read10_count,))
        print("3次メッシュDEMファイル数: %d" % (opt.read5_count,))
        if opt.output10_count > 0:
            print("出力2次メッシュ単位 GeoTiff ファイル数: %d" % (opt.output10_count,))
        if opt.output5_count > 0:
            print("出力3次メッシュ単位 GeoTiff ファイル数: %d" % (opt.output5_count,))
        en = datetime.now()
        print("処理時間 %s" % (en - st,))
    except CommandException as ex:
        print(ex)
        sys.exit(1)
