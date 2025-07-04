from photutils.detection import DAOStarFinder
from astropy.stats import sigma_clipped_stats
import numpy as np

import file_utils
import json

def find_star(image_data, fwhm=3.0, threshold_factor=5.0) -> np.ndarray:
    # 估算背景与噪声
    mean, median, std = sigma_clipped_stats(image_data, sigma=3.0)
    # 找星（设置合适的阈值）
    daofind = DAOStarFinder(fwhm=fwhm, threshold=threshold_factor * std)
    # 使用背景减去中位数来提高星点检测的准确性
    return daofind(image_data - median)

if __name__ == '__main__':

    paths = file_utils.get_fits_file_paths('data/')

    FILE_NUM = 49  # 选择要处理的文件编号
    img_data, hdr = file_utils.read_image_data(paths[FILE_NUM])  # 选择第50张图像

    clip_image_fixed, clip_image_percentile, clip_image_statistics = file_utils.clip_image_data(img_data)

    source0 = find_star(img_data)
    source1 = find_star(clip_image_fixed)
    source2 = find_star(clip_image_percentile)
    source3 = find_star(clip_image_statistics)

    # 过滤 sharpness 太低 或 roundness1 太大的星点
    roundness_threshold = 0.5
    sharpness_threshold = 0.3
    source0 = source0[(source0['sharpness'] > sharpness_threshold) & (np.abs(source0['roundness1']) < roundness_threshold)]
    source1 = source1[(source1['sharpness'] > sharpness_threshold) & (np.abs(source1['roundness1']) < roundness_threshold)]
    source2 = source2[(source2['sharpness'] > sharpness_threshold) & (np.abs(source2['roundness1']) < roundness_threshold)]
    source3 = source3[(source3['sharpness'] > sharpness_threshold) & (np.abs(source3['roundness1']) < roundness_threshold)]

    # 将 header 保存到json文件
    with open(f'result/find_star/header_{FILE_NUM}.json', 'w') as f:
        json.dump(dict(hdr), f, indent=4)

    np.save('result/find_star/source_fixed.npy', source1)
    np.save('result/find_star/source_percentile.npy', source2)
    np.save('result/find_star/source_statistics.npy', source3)

    print(f'原始图像找到 {len(source0)} 个星点')
    print(f'固定值裁剪找到 {len(source1)} 个星点')
    print(f'百分位裁剪找到 {len(source2)} 个星点')
    print(f'统计量裁剪找到 {len(source3)} 个星点')

    # 按照光度排序并取前10个星点
    TOP = 100
    top_flux_origin = source0[np.argsort(source0['flux'])[-TOP:]]
    top_flux_fixed = source1[np.argsort(source1['flux'])[-TOP:]]
    top_flux_percentile = source2[np.argsort(source2['flux'])[-TOP:]]
    top_flux_statistics = source3[np.argsort(source3['flux'])[-TOP:]]

    # 在图像中圈出前10个星点
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 2, 1)
    plt.imshow(img_data, origin='lower')
    plt.scatter(top_flux_origin['xcentroid'],
                top_flux_origin['ycentroid'],
                s=top_flux_origin['npix'],
                edgecolor='red',
                facecolor='none',
                label=f'Top {TOP} Flux')
    plt.title('Original Image Stars')
    plt.legend()
    plt.subplot(2, 2, 2)
    plt.imshow(clip_image_fixed, origin='lower')
    plt.scatter(top_flux_fixed['xcentroid'],
                top_flux_fixed['ycentroid'],
                s=top_flux_fixed['npix'],
                edgecolor='red',
                facecolor='none',
                label=f'Top {TOP} Flux')
    plt.title('Fixed Clipping Stars')
    plt.legend()
    plt.subplot(2, 2, 3)
    plt.imshow(clip_image_percentile, origin='lower')
    plt.scatter(top_flux_percentile['xcentroid'],
                top_flux_percentile['ycentroid'],
                s=top_flux_percentile['npix'],
                edgecolor='red',
                facecolor='none',
                label=f'Top {TOP} Flux')
    plt.title('Percentile Clipping Stars')
    plt.legend()
    plt.subplot(2, 2, 4)
    plt.imshow(clip_image_statistics, origin='lower')
    plt.scatter(top_flux_statistics['xcentroid'],
                top_flux_statistics['ycentroid'],
                s=top_flux_statistics['npix'],
                edgecolor='red',
                facecolor='none',
                label=f'Top {TOP} Flux')
    plt.title('Statistics Clipping Stars')
    plt.legend()
    plt.tight_layout() # 自动调整子图间距
    plt.show()

