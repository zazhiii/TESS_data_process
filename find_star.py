from photutils.detection import DAOStarFinder
from astropy.stats import sigma_clipped_stats
import numpy as np


def find_star(image_data, fwhm=3.0, threshold_factor=5.0) -> np.ndarray:
    # 估算背景与噪声
    mean, median, std = sigma_clipped_stats(image_data, sigma=3.0)
    # 找星（设置合适的阈值）
    daofind = DAOStarFinder(fwhm=fwhm, threshold=threshold_factor * std)
    # 使用背景减去中位数来提高星点检测的准确性
    return daofind(image_data - median)


if __name__ == '__main__':
    import file_utils
    # 文件列表
    folder = "data/"
    FILE_NUM = 49 # 选择要处理的文件编号
    fits_file_names = file_utils.get_fits_file_names(folder)
    img_data = file_utils.read_image_data(folder + fits_file_names[FILE_NUM])
    clip_image_fixed, clip_image_percentile, clip_image_statistics = file_utils.clip_image_data(img_data)

    source1 = find_star(clip_image_fixed)
    source2 = find_star(clip_image_percentile)
    source3 = find_star(clip_image_statistics)

    print(f'固定值裁剪找到 {len(source1)} 个星点')
    print(f'百分位裁剪找到 {len(source2)} 个星点')
    print(f'统计量裁剪找到 {len(source3)} 个星点')

