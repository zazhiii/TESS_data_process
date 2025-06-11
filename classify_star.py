import numpy as np
from astroquery.gaia import Gaia
import pandas as pd

from tqdm import tqdm
from astroquery.mast import Catalogs
from astropy.coordinates import SkyCoord
import astropy.units as u
import file_utils
from astropy.io import fits
from astropy.wcs import WCS
import logging
from astroquery.gaia import Gaia

# 设置日志记录为 error级别
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

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

    folder = "data/"
    FILE_NUM = 49 # 选择要处理的文件编号
    fits_file_names = file_utils.get_fits_file_names(folder)
    hdul = fits.open(folder + fits_file_names[FILE_NUM])
    wcs = WCS(hdul[1].header)

    source_origin = np.load('result/find_star/source_origin.npy', allow_pickle=True)
    print(f"读取到 {len(source_origin)} 个星点数据")

    ids = pd.read_csv('result/light_curves/data/feat.csv')['id'].tolist()
    print(f"其中需要查询的星点数量: {len(ids)}")

    start_num = 554 + 54 + 1050

    for ID in tqdm(ids[start_num:], desc="处理每个星点", unit="id", colour="green"):
        # 假设你有一个星点的像素位置：
        x_pix, y_pix = source_origin[ID]['xcentroid'], source_origin[ID]['ycentroid']

        # 转为 RA/Dec（FITS 标准 origin=1）
        ra, dec = wcs.all_pix2world(x_pix, y_pix, 1)
        print(f"RA = {ra:.6f}, Dec = {dec:.6f}")

        # 构造 SkyCoord
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
        # 查询 TIC catalog，默认 10 arcsec，返回最匹配对象
        tic_result = Catalogs.query_region(coord, catalog="TIC", radius=5 * u.arcsec)
        tic_id = None
        source_id = None
        if len(tic_result) > 0:
            tic_id = tic_result[0]['ID']
            source_id = tic_result[0]['GAIA']
            print(f"TIC ID: {tic_id}, GAIA DR3 source_id: {source_id}")
        else:
            print("未匹配到 TIC 恒星")
            continue

        query = f"""
        SELECT best_class_name, best_class_score
        FROM gaiadr3.vari_classifier_result
        WHERE source_id = {source_id}
        """

        job = Gaia.launch_job_async(query)
        result = job.get_results()

        if len(result) > 0:
            star_type = result['best_class_name'][0]
            score = result['best_class_score'][0]
            print(f"该星被分类为：{star_type}，置信度：{score:.2f}")
        else:
            print("该源未被 Gaia DR3 标记为变星")

        # 将结果追加到 CSV 文件中
        res = {
            'id': ID,
            'tic_id': tic_id,
            'source_id': source_id,
            'ra': ra,
            'dec': dec,
            'best_class_name': result['best_class_name'][0] if len(result) > 0 else None,
            'best_class_score': result['best_class_score'][0] if len(result) > 0 else None,
        }
        df = pd.DataFrame([res])
        df.to_csv('result/light_curves/data/feat_classify.csv', mode='a', header=False, index=False)
