import matplotlib.pyplot as plt
from astropy.stats import sigma_clipped_stats

import file_utils
import numpy as np
from find_star import find_star
from tqdm import tqdm
from scipy.ndimage import median_filter
from astropy.timeseries import LombScargle

def get_light_curve(fits_file_paths: list,
                    source: any,
                    box_size: int = 5) -> tuple:
    fluxes = [[] for _ in range(len(source))]
    times = []
    for path in tqdm(fits_file_paths, desc="从 FITS 文件中提取每个星的光度", unit="file", colour="green"):

        image_data, header = file_utils.read_image_data(path)
        times.append(header['TSTART']) # 获取时间戳

        # 使用中值滤波来减少噪声
        image_data = median_filter(image_data, size=3)
        # 计算图像的统计量
        mean, median, std = sigma_clipped_stats(image_data, sigma=3.0)
        # 计算每个星点在当前图像中的光度
        for i, (x, y) in enumerate(zip(source['xcentroid'], source['ycentroid'])):
            half = box_size // 2
            # 计算指定位置的光度
            sub_image = image_data[int(y - half):int(y + half + 1), int(x - half):int(x + half + 1)]
            flux = np.sum(sub_image - median)  # 减去背景中值
            fluxes[i].append(flux)
    return fluxes, times

if __name__ == '__main__':

    paths = file_utils.get_fits_file_paths('data/')

    # 去除前 25 张图像
    paths = paths[25:]
    print(f'读取到 {len(paths)} 个 FITS 文件')

    sc = np.load('result/find_star/source_fixed.npy', allow_pickle=True)
    print(f'读取到 {len(sc)} 个星点数据')

    fs, ts = get_light_curve(paths, sc)

    # 索引 121 位置处异常
    for f in fs:
        f[121] = (f[120] + f[122]) / 2  # 简单插值修正

    np.save('result/light_curves/data/fluxes.npy', fs)
    np.save('result/light_curves/data/times.npy', ts)

    # for flux in fs:
    #     plt.figure(figsize=(10, 5))
    #     plt.plot(flux, label='Star 0', color='blue')
    #     plt.title('Light Curve of Star 0')
    #     plt.xlabel('Time (days)')
    #     plt.ylabel('Flux')
    #     plt.grid()
    #     plt.legend()
    #     plt.show()

