# 1818 食双星 source_id = 38570936622030848
# 7365
# 1388 …… 正弦型，短周期
# 1193 …… 周期稍长
# 1342 …… 单个凸起
# 2994 …… 周期更长
# 6725
# 6897
from importlib.util import source_hash

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord, match_coordinates_sky
from astropy.wcs import WCS, FITSFixedWarning
from astroquery.gaia import Gaia
import astropy.units as u
from tqdm import tqdm
import warnings
import logging
warnings.filterwarnings('ignore', category=FITSFixedWarning)
logging.getLogger('astroquery').setLevel(logging.ERROR)  # 设置 astroquery 的日志级别为 ERROR，避免输出过多信息

def query_star(id, x, y, hdr):
    wcs = WCS(hdr)
    ra, dec = wcs.all_pix2world(x, y, 1)
    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    job = Gaia.cone_search_async(coordinate=coord, radius=100 * u.arcsec)  # 半径100 arcsec
    results = job.get_results()
    results.sort('dist')
    if len(results) > 0:
        source_id = results[0]['source_id']
        return {
            'id': id,
            'source_id': source_id,
            'ra': ra,
            'dec': dec,
            'xcentroid': x,
            'ycentroid': y
        }


if __name__ == '__main__':
    import file_utils

    # 文件列表
    folder = "data/"
    FILE_NUM = 49  # 选择要处理的文件编号
    fits_file_names = file_utils.get_fits_file_names(folder)
    img_data, hdr = file_utils.read_image_data(folder + fits_file_names[FILE_NUM])

    # 从.npy文件中读取星点数据
    sources = np.load('result/find_star/source_statistics.npy', allow_pickle=True)

    feats = pd.read_csv('result/light_curves/feat.csv')

    # 取出 id 列的数据
    ids = feats['id'].values

    print(ids)

    source_info_list = []
    s, e = 101, 200
    for i, ID in enumerate(tqdm(ids[s:e], desc="查询每个星点的 source_id", unit="source", colour="blue")):
        x, y = sources[ID]['xcentroid'], sources[ID]['ycentroid']
        res = query_star(ID, x, y, hdr)
        source_info_list.append(res)
    # 保存到 CSV 文件中
    sources_info = pd.DataFrame(source_info_list)
    sources_info.to_csv(f'result/sources_info_{s}-{e}.csv', index=False)

    classify_res = []
    classify_name_map = {
        'RRAB': 'RR Lyrae',
        'RR': 'RR Lyrae',
        'DSCT': 'Delta Scuti',
        'ECL': '食双星',
        'MIRA': '长周期变星',
        'SR': '长周期变星',
        'CEP': '造父变星',
        'Other': '其他变星',
    }

    #
    # idx_s, idx_e = 0, 10
    # for i, source in enumerate(tqdm(sources[idx_s:idx_e + 1], desc="处理每个星点", unit="source", colour="blue")):
    #     # 取出像素坐标
    #     x, y = source['xcentroid'], source['ycentroid']
    #
    #     # 转换为天球坐标（单位为度）
    #     wcs = WCS(hdr)
    #     ra, dec = wcs.all_pix2world(x, y, 1)
    #
    #     coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    #     # 进行 Gaia 锥形查询（半径例如 5 arcsec）
    #     job = Gaia.cone_search_async(coordinate=coord, radius=100 * u.arcsec)
    #     results = job.get_results()
    #
    #     # 按照距离排序
    #     results.sort('dist')
    #
    #     # 取出距离最近的一个
    #     if len(results) > 0:
    #         source_id = results[0]['source_id']
    #
    #         # 获取 Gaia DR3 中的变星分类结果
    #         query = f"""
    #         SELECT *
    #         FROM gaiadr3.vari_classifier_result
    #         WHERE source_id = {source_id}
    #         """
    #         job = Gaia.launch_job_async(query)
    #         result = job.get_results()
    #
    #         if len(result) > 0:
    #             classify_res.append({
    #                 'source_id': source_id,
    #                 'best_class_name': result["best_class_name"][0],
    #                 'best_class_score': result["best_class_score"][0],
    #                 'name': classify_name_map.get(result["best_class_name"][0], '其他变星'),
    #             })
    #
    # pd.DataFrame(classify_res).to_csv('result/identify_system.csv', index=False)
