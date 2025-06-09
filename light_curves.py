import matplotlib.pyplot as plt
import file_utils
import numpy as np
from find_star import find_star
from tqdm import tqdm
from scipy.ndimage import median_filter
from astropy.timeseries import LombScargle

def get_light_curve(fits_file_paths: list,
                    source: any,
                    box_size: int = 7) -> tuple[list, list]:
    """
    从 FITS 文件中提取每个星点的光度曲线
    :param fits_file_paths: 文件路径列表
    :param source: 星点信息，通常是一个包含星点位置的 DataFrame 或类似结构
    :param box_size: 用于计算光度的方形区域大小，默认为 7
    :return: 光度曲线列表和时间列表
    """

    # 过滤 sharpness 太低 或 roundness1 太大的星点, TODO: 根据实际情况调整阈值
    # filter_source = source[(source['sharpness'] > 0.2) & (np.abs(source['roundness1']) < 1.0)]
    # print(f'过滤后剩余 {len(filter_source)} 个星点')

    fluxes = [[] for _ in range(len(source))]
    time = []

    for path in tqdm(fits_file_paths, desc="从 FITS 文件中提取每个星的光度", unit="file", colour="green"):

        image_data, header = file_utils.read_image_data(path)
        time.append(header['TSTART'])  # 假设 TSTART 存在于头信息中

        # 计算每个星点在当前图像中的光度
        i = 0
        for x, y in zip(source['xcentroid'], source['ycentroid']):
            half = box_size // 2
            # 计算指定位置的光度
            sub_image = image_data[int(y - half):int(y + half + 1), int(x - half):int(x + half + 1)]
            flux = np.sum(sub_image)
            fluxes[i].append(flux)
            i += 1

    return fluxes, time

if __name__ == '__main__':
    # 获取文件路径列表
    folder = "data/"
    fits_file_names = file_utils.get_fits_file_names(folder)
    fits_file_paths = [folder + name for name in fits_file_names]

    # TODO: 先做第 50 张图（除第 147 张图）之后的处理，前面一部分图片有问题
    fits_file_paths = fits_file_paths[49:146] + fits_file_paths[147:]
    print(f'读取到 {len(fits_file_paths)} 个 FITS 文件')

    # 找星
    FILE_NUM = 0
    image_data, header = file_utils.read_image_data(fits_file_paths[FILE_NUM])
    clip_image_data = file_utils.stats_clip_image_data(image_data)
    source = find_star(clip_image_data)
    print(f'找到 {len(source)} 个星点')

    BOX_SIZE = 7  # 方形区域大小
    fluxes, time = get_light_curve(fits_file_paths, source, BOX_SIZE)

    # 保存到 npy 文件
    np.save('result/light_curves/fluxes.npy', fluxes)
    np.save('result/light_curves/time.npy', time)

