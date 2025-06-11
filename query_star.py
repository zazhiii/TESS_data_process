
import json

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS, FITSFixedWarning
from astroquery.gaia import Gaia
import astropy.units as u
from tqdm import tqdm

from classify_star import query_single_classify
import warnings
warnings.simplefilter('ignore', FITSFixedWarning)
import logging
# 设置日志记录为 error级别
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


def query_star(id, x, y, hdr):
    wcs = WCS(hdr)
    ra, dec = wcs.all_pix2world(x, y, 0)
    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    job = Gaia.cone_search_async(coordinate=coord, radius=100 * u.arcsec)  # 半径100 arcsec
    results = job.get_results()
    results.sort('dist')
    print(f'查询 {id} 的星点，位置：({ra:.6f}, {dec:.6f})，找到 {len(results)} 个结果')
    if len(results) > 0:
        source_id = results[0]['source_id']
        return {
            'id': id,
            'source_id': source_id,
            'ra': ra,
            'dec': dec
        }

# 从.npy文件中读取星点数据
if __name__ == '__main__':

    # 加载头信息
    with open('result/light_curves/header.json', 'r') as f:
        hdr = json.load(f)
    sources = np.load('result/find_star/source_origin.npy', allow_pickle=True)
    print(f"读取到 {len(sources)} 个星点数据")

    ids = pd.read_csv('result/light_curves/data/feat.csv')['id'].tolist()

    start_num = 0 # len(feat_classify.csv)

    for ID in tqdm(ids[start_num:], desc="处理每个星点", unit="id", colour="green"):
        x, y = sources[ID]['xcentroid'], sources[ID]['ycentroid']

        print(f"查询的星: id: {ID}, x: {x}, y: {y}")
        star_info = query_star(ID, x, y, hdr)

        sid = star_info['source_id']
        print(f"查询到的星点信息: {star_info}")

        query_res = query_single_classify(sid)
        print(f"查询结果: {query_res}")
        # 追加到 csv 文件中
        res = {
            'id': ID,
            'source_id': sid,
            'x': x,
            'y': y,
            'ra': star_info['ra'],
            'dec': star_info['dec'],
            'best_class_name': query_res['best_class_name'] if len(query_res) > 0 else None,
            'best_class_score': query_res['best_class_score'] if len(query_res) > 0 else None,
            'classifier_name': query_res['classifier_name'] if len(query_res) > 0 else None,
        }
        # # 将结果追加到 CSV 文件中
        df = pd.DataFrame([res])
        df.to_csv('result/light_curves/data/feat_classify.csv', mode='a', header=False, index=False)




