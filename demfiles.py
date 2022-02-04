import os
import numpy as np
import re

def enum_demfiles(dem_dir):
    """dem_dir で指定したディレクトリ配下にある DEM ファイルを
    DEM10, DEM5 に分けて取得する。
    取得単位は DEM10 単位で、その配下にある DEM5 ファイルを 10x10
    の配列として取得する

    Args:
        dem_dir (str): 取得する DEMファイルが存在するディレクトリ (階層は問わない)
    
    Yields:
        mesh2, dem10_path, dem5_array
    
        mesh2 は２次メッシュ
        dem10_path は DEM10 ファイルのパス
        dem5_array は DEM5 ファイルのパスが入っている 10x10 の numpy array
    """
    pat5 = r"FG-GML-(\d{4}-\d{2})-(\d{2})-(\w+).+\.xml"
    pat10 = r"FG-GML-(\d{4}-\d{2})-(\w+).+\.xml"
    def choose(new, org):
        if org is None:
            return new
        #print("Choose between %s, %s path=%s" % (new[0], org[0], os.path.split(new[1])[1]))
        return org if (new[0] < org[0]) else new
    files5 = {}
    files10 = {}
    for root, dirs, files in os.walk(dem_dir):
        for file in files:
            mo = re.match(pat5, file)
            if mo:
                mesh2 = mo.group(1)
                mesh3 = mo.group(2)
                demtype = mo.group(3).upper()
                fullpath = os.path.join(root, file)
                key = (mesh2, mesh3)
                files5[key] = choose((demtype, fullpath), files5.get(key, None))
            else:
                mo = re.match(pat10, file)
                if mo:
                    mesh2 = mo.group(1)
                    demtype = mo.group(2).upper()
                    fullpath = os.path.join(root, file)
                    files10[mesh2] = choose((demtype, fullpath), files10.get(mesh2, None))
    map10_5 = {}
    for (mesh2, mesh3), (files5type, files5_path) in files5.items():
        y, x = int(mesh3[0]), int(mesh3[1])
        try:
            mx = map10_5[mesh2]
        except KeyError:
            mx = np.full((10, 10), None)
            map10_5[mesh2] = mx
        mx[y, x] = files5_path
    for mesh2, dem10val in files10.items():
        dem10_path = dem10val[1]
        try:
            mx = map10_5[mesh2]
        except KeyError:
            mx = np.full((10, 10), None)
        yield mesh2, dem10_path, mx
