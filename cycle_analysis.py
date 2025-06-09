import os

import numpy as np
from astropy.timeseries import LombScargle
import pandas as pd
from tqdm import tqdm

from matplotlib import pyplot as plt

if __name__ == '__main__':
    output_csv = 'result/light_curves/feat.csv'
    figures_dir = 'result/light_curves/figures'
    os.makedirs(figures_dir, exist_ok=True)

    # 从 npy 文件加载光度曲线数据 allow_pickle=True 允许加载包含 Python 对象的数组
    fluxes = np.load('result/light_curves/fluxes.npy', allow_pickle=True)
    time = np.load('result/light_curves/time.npy', allow_pickle=True)

    feat_list = []
    i = 0
    for i, flux in enumerate(tqdm(fluxes, desc='处理光度曲线')):
        std = np.std(flux) # 计算标准差
        ptp = np.ptp(flux) # 计算极差
        # 定义频率范围（单位是 cycles per day）
        min_period = 0.05 # 最小周期（day）
        max_period = 10 # 最大周期（day）
        frequency, power = LombScargle(time, flux).autopower(
            minimum_frequency = 1 / max_period,
            maximum_frequency = 1 / min_period,
            # samples_per_peak=10  # 每个周期采样点数
        )
        # 找到周期峰值
        best_frequency = frequency[np.argmax(power)]
        best_period = 1 / best_frequency # 计算最佳周期（单位是天）

        # 周期异常，说明该光度曲线没有明显的周期性
        if best_period <= min_period or best_period >= max_period:
            continue

        max_power = np.max(power) # 最大功率

        is_special = int(std > 0.005 and max_power > 0.2 and 0.3 < best_period < 10)

        feat_list.append(
            {
                'id': i,
                'std': std,
                'ptp': ptp,
                'max_power': max_power,
                'best_frequency': best_frequency,
                'best_period': best_period,
                'is_special': is_special
            }
        )

        # 绘制光度曲线图并保存
        plt.figure(figsize=(10, 5))
        plt.plot(time, flux)
        plt.title(f'light_curves {i} - std: {std:.4f}, ptp: {ptp:.4f}, max_power: {max_power:.4f}, best_period: {best_period:.4f}')
        plt.xlabel('Time(day)')
        plt.ylabel('Flux')
        plt.grid()
        plt.savefig(f'{figures_dir}/light_curve_{i}_period-{best_period:.4f}.png')
        plt.close()

    # 保存特征到 CSV 文件
    df = pd.DataFrame(feat_list)
    df.to_csv(output_csv, index=False)
    print(f'特征已保存到 {output_csv}')
