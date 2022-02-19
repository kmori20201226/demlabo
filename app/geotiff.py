import os
from osgeo import gdal
from osgeo import osr # 空間参照モジュール
from demreader import D0

def write_geotiff(output_fname, plane, d0:D0):
    output = gdal.GetDriverByName('GTiff').Create(
        output_fname, 
        plane.shape[1], 
        plane.shape[0], 
        1, 
        gdal.GDT_Float32, 
        options = ['PHOTOMETRIC=MINISBLACK'])
    output.SetGeoTransform(
        (
            d0.W,
            (d0.E - d0.W) / (d0.highx - d0.lowx + 1),
            0,
            d0.N,
            0,
            -(d0.N - d0.S) / (d0.highy - d0.lowy + 1)
        ))
    srs = osr.SpatialReference() # 空間参照情報
    srsEpsg = 6668 if d0.srs == "fguuid:jgd2011.bl" else 4612
    srs.ImportFromEPSG(srsEpsg)
    output.SetProjection(srs.ExportToWkt()) # 空間情報を結合
    output.GetRasterBand(1).WriteArray(plane)
    output.FlushCache() 

