import json

import numpy as np
import pandas as pd

from tqdm import tqdm
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.wcs import WCS
import logging
from astroquery.gaia import Gaia

# 设置日志记录为 error级别
logging.getLogger('astroquery').setLevel(logging.ERROR)

def query_single_classify(source_id):
    query = f"""
        SELECT *
        FROM gaiadr3.vari_classifier_result
        WHERE source_id = {source_id}
    """
    job = Gaia.launch_job_async(query)
    result = job.get_results()
    return result

if __name__ == '__main__':
    output_path = 'result/light_curves/data/feat_classify.csv'

    hdr = json.load(open('result/find_star/header_49.json', 'r'))
    wcs = WCS(hdr)

    source = np.load('result/find_star/source_fixed.npy', allow_pickle=True)
    print(f"读取到 {len(source)} 个星点数据")

    ids = pd.read_csv('result/light_curves/feat.csv')['id'].tolist()
    print(f"其中需要查询的星点数量: {len(ids)}")

    # 已经查询过确定没有的 source_id
    queried_ids = pd.read_csv('result/light_curves/data/feat_classify.csv')['id'].tolist()
    print(f"已经查询过：{queried_ids}")

    for ID in tqdm(ids, desc="处理每个星点", unit="id", colour="green"):

        if ID in queried_ids:
            print(f"ID {ID} 已经查询过，跳过")
            continue

        # 假设你有一个星点的像素位置：
        x_pix, y_pix = source[ID]['xcentroid'], source[ID]['ycentroid']

        # 转为 RA/Dec（FITS 标准 origin=1）
        ra, dec = wcs.all_pix2world(x_pix, y_pix, 1)
        print(f"RA = {ra:.6f}, Dec = {dec:.6f}")

        coord = SkyCoord(ra, dec, unit=(u.deg, u.deg), frame='icrs')

        width = u.Quantity(100, u.arcsec)
        j = Gaia.cone_search_async(coord, radius=width)
        r = j.get_results()

        r.sort('dist')

        print(f"查询到 {len(r)} 个 Gaia 源, 最近的距离为 {r[0]['dist']:.4f} arcsec")

        if len(r) > 0:
            source_id = r[0]['source_id']
            print("Matched Gaia source_id:", source_id)
        else:
            print("No Gaia source found.")
            # 将结果追加到 CSV 文件中
            res = {
                'id': ID,
                'source_id': '未找到',
                'ra': ra,
                'dec': dec,
                'best_class_name': '',
                'best_class_score': '',
            }
            df = pd.DataFrame([res])
            df.to_csv(output_path, mode='a', header=False, index=False)
            continue

        result = query_single_classify(source_id)

        if len(result) > 0:
            star_type = result['best_class_name'][0]
            score = result['best_class_score'][0]
            print(f"该星被分类为：{star_type}，置信度：{score:.2f}")
        else:
            print("该源未被 Gaia DR3 标记为变星")

        # 将结果追加到 CSV 文件中
        res = {
            'id': ID,
            'source_id': source_id,
            'ra': ra,
            'dec': dec,
            'best_class_name': result['best_class_name'][0] if len(result) > 0 else "未分类",
            'best_class_score': result['best_class_score'][0] if len(result) > 0 else "未分类",
            'dist': r[0]['dist'],
        }
        df = pd.DataFrame([res])
        df.to_csv('result/light_curves/data/feat_classify.csv', mode='a', header=False, index=False)
