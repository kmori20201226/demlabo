"""指定したディレクトリ配下の全 DEM ファイルの内容を表示する
指定ディレクトリの下のDEMは任意の階層に存在可能。FG-GML*.xml で検索される

"""
import os
import re
from tqdm import tqdm
import numpy as np
from demreader import dem2image
from demfiles import enum_demfiles

def list_dems(dem_dir):
    for mesh2, dem10_path, dem5_array in enum_demfiles(dem_dir):
        dem10 = dem2image(dem10_path, noimage=True)[1]
        print(dem10_path, dem10)
        for y in range(10):
            for x in range(10):
                dem5_path = dem5_array[y, x]
                if dem5_path is not None:
                    dem5 = dem2image(dem5_path, noimage=True)[1]
                    print("    %s:%s" % (dem5_path, dem5))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("dem_dir", type=str, help="DEMファイルが格納されているディレクトリ")
    args = parser.parse_args()
    list_dems(args.dem_dir)