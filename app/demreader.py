"""DEMデータ読み込みモジュール

DEM データ例
~~~~~~~~~~~~~
.. code::

    <?xml version="1.0" encoding="UTF-8"?>

    <Dataset xsi:schemaLocation="http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema FGD_GMLSchema.xsd" 
        xmlns:gml="http://www.opengis.net/gml/3.2" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
        xmlns:xlink="http://www.w3.org/1999/xlink" 
        xmlns="http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema" 
        gml:id="Dataset1">
        <gml:description>基盤地図情報メタデータ ID=fmdid:15-3101</gml:description>
        <gml:name>基盤地図情報ダウンロードデータ（GML版）</gml:name>
        
        <DEM gml:id="DEM001">
            <fid>fgoid:10-00100-15-60101-50302300</fid>
            <lfSpanFr gml:id="DEM001-1">
                <gml:timePosition>2016-10-01</gml:timePosition>
            </lfSpanFr>
            <devDate gml:id="DEM001-2">
                <gml:timePosition>2016-10-01</gml:timePosition>
            </devDate>
            <orgGILvl>0</orgGILvl>
            <orgMDId>H22I0021</orgMDId>
            <type>5mメッシュ（標高）</type>
            <mesh>50302300</mesh>
            <coverage gml:id="DEM001-3">
                <gml:boundedBy>
                    <gml:Envelope srsName="fguuid:jgd2011.bl">
                        <gml:lowerCorner>33.5 130.375</gml:lowerCorner>
                        <gml:upperCorner>33.508333333 130.3875</gml:upperCorner>
                    </gml:Envelope>
                </gml:boundedBy>
                <gml:gridDomain>
                    <gml:Grid dimension="2" gml:id="DEM001-4">
                        <gml:limits>
                            <gml:GridEnvelope>
                                <gml:low>0 0</gml:low>
                                <gml:high>224 149</gml:high>
                            </gml:GridEnvelope>
                        </gml:limits>
                        <gml:axisLabels>x y</gml:axisLabels>
                    </gml:Grid>
                </gml:gridDomain>
                <gml:rangeSet>
                    <gml:DataBlock>
                        <gml:rangeParameters>
                            <gml:QuantityList uom="DEM構成点"></gml:QuantityList>
                        </gml:rangeParameters>

    <gml:tupleList>
    地表面,360.97
    地表面,359.76
    ...

    地表面,156.15
    地表面,156.03
    </gml:tupleList>

                    </gml:DataBlock>
                </gml:rangeSet>
                <gml:coverageFunction>
                    <gml:GridFunction>
                        <gml:sequenceRule order="+x-y">Linear</gml:sequenceRule>
                        <gml:startPoint>0 0</gml:startPoint>
                    </gml:GridFunction>
                </gml:coverageFunction>
            </coverage>
        </DEM>
    </Dataset>

"""
from xml.etree import ElementTree as ET
import numpy as np

class D0:
    """DEM ファイルから読み込まれたメタデータ

    Attributes:
        type (str): タイプ
        mesh (str): メッシュコード
        srs  (str): source spatial reference
        S (float): 南端緯度
        N (float): 北端緯度
        W (float): 西端経度
        E (float): 東端緯度
        lowx (int): 左端ピクセル位置
        lowy (int): 下端ピクセル位置
        highx (int): 右端ピクセル位置
        highy (int): 左端ピクセル位置
        nodata_cnt (int|None): 欠落値数
    """
    def __init__(self):
        self.type = None
        self.mesh = None
        self.srs = None
        self.S = None
        self.N = None
        self.E = None
        self.W = None
        self.lowx = None
        self.lowy = None
        self.highx = None
        self.highy = None
        self.nodata_cnt = None
    
    def __repr__(self):
        return "%s[%s,%s,%s,%s](%s,%s)-(%s,%s)" % (
            self.mesh,
            self.N, self.E, self.S, self.W,
            self.lowx, self.lowy, self.highx, self.highy
        )

def dem2image(input_file, nodata=np.nan, noimage=False):
    """DEMファイルを読み込み shapeが(y,x) の np.array を作る

    Args:
        input_file (str): DEM ファイル名
        nodata (bool): 設定する欠落値 (DEMファイル自身は-9999が欠落値として規定されている)
        noimage (bool): 新であれば イメージを表す np.array を作らない (戻り値としてはNone)    

    Returns:
        イメージデータ (np.array), メタデータ (D0)
    """
    def get2d(s):
        return (float(x) for x in s.text.split(" "))
    def get2i(s):
        return (int(x) for x in s.text.split(" "))
    tree = ET.parse(input_file)
    ns = {
        "": "http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema", 
        "gml": "http://www.opengis.net/gml/3.2"
    }
    root = tree.getroot()
    d0 = D0()
    d0.type = root.find("./DEM/type", ns).text
    d0.mesh = root.find("./DEM/mesh", ns).text
    b_envelope = root.find("./DEM/coverage/gml:boundedBy/gml:Envelope", ns)
    d0.srs = b_envelope.attrib['srsName']
    d0.S, d0.W = get2d(b_envelope.find("./gml:lowerCorner", ns))
    d0.N, d0.E = get2d(b_envelope.find("./gml:upperCorner", ns))
    domain = root.find("./DEM/coverage/gml:gridDomain/gml:Grid/gml:limits/gml:GridEnvelope", ns)
    d0.lowx, d0.lowy = get2i(domain.find("./gml:low", ns))
    d0.highx, d0.highy = get2i(domain.find("./gml:high", ns))
    tuplist = root.find("./DEM/coverage/gml:rangeSet/gml:DataBlock/gml:tupleList", ns)
    dshape = (d0.highy - d0.lowy + 1, d0.highx - d0.lowx + 1) 
    startx, starty = get2i(root.find("./DEM/coverage/gml:coverageFunction/gml:GridFunction/gml:startPoint", ns))
    snum = (d0.highx + 1) * starty + startx
    nodata_cnt = snum
    if not noimage:
        astring = np.empty(dshape[0]*dshape[1], np.float32)
        astring.fill(nodata)
        altvec = []
        for line in tuplist.text.split("\n"):
            if line.strip() != "":
                larr = line.strip().split(",")
                v = float(larr[1])
                if v == -9999:
                    nodata_cnt += 1
                    altvec += [nodata]
                else:
                    altvec += [v]
        altarr = np.array(altvec, np.float32)
        astring[snum:snum+altarr.shape[0]] = altarr
        plane = astring.reshape(dshape)
        d0.nodata_cnt = nodata_cnt
    else:
        plane = None
    return plane, d0

