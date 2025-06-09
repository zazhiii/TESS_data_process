import os
import numpy as np
from astropy.stats import sigma_clipped_stats

def get_fits_file_names(folder_path: str) -> list:
    try:
        files = os.listdir(folder_path)
    except FileNotFoundError:
        print(f"Error: 文件夹 '{folder_path}' 不存在或无法访问。")
        return []
    res = [f for f in files if f.endswith('.fits')]
    return sorted(res)

def read_image_data(fit_file_path: str) -> tuple[np.ndarray, dict]:
    from astropy.io import fits
    with fits.open(fit_file_path) as hdulist:
        # 提取图像数据和头信息
        image_data = hdulist[1].data
        hdr = hdulist[1].header
        # 去除边框
        return image_data[0:-45, 45:-45], hdr

def fixed_clip_image_data(image_data: np.ndarray, a_min: float = 100, a_max: float = 400) -> np.ndarray:
    return np.clip(image_data, a_min=a_min, a_max=a_max)

def stats_clip_image_data(image_data: np.ndarray, sigma: float = 3.0) -> np.ndarray:
    mean, median, std = sigma_clipped_stats(image_data, sigma=sigma)
    vmin = median - 1 * std
    vmax = median + 5 * std
    return np.clip(image_data, vmin, vmax)

def clip_image_data(image_data: np.ndarray) -> tuple:
    clip_image_fixed = np.clip(image_data, a_min=100, a_max=400)

    vmin = np.percentile(image_data, 1)  # 下限设为第1百分位
    vmax = np.percentile(image_data, 99)  # 上限设为第99百分位
    clip_image_percentile = np.clip(image_data, vmin, vmax)

    mean, median, std = sigma_clipped_stats(image_data, sigma=3.0)
    vmin = median - 1 * std
    vmax = median + 5 * std
    clip_image_statistics = np.clip(image_data, vmin, vmax)

    return clip_image_fixed, clip_image_percentile, clip_image_statistics

if __name__ == '__main__':
    # 测试代码
    folder = "data/"
    fits_file_names = get_fits_file_names(folder)
    img_data, hdr = read_image_data(folder + fits_file_names[0])

    # print(hdr)

    # 优先使用 TSTART
    if 'TSTART' in hdr:
        time = hdr['TSTART']  # 单位：BTJD（Barycentric TESS Julian Date）
        print(f"TSTART: {time}")
        # 转换格式
    elif 'DATE-OBS' in hdr:
        from astropy.time import Time
        time = Time(hdr['DATE-OBS'], format='isot').btjd
        print(f"DATE-OBS: {time}")
    else:
        print("Error: FITS header does not contain TSTART or DATE-OBS.")