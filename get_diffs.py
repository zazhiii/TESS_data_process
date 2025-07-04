import numpy as np
from astropy.io import fits
from photutils.detection import DAOStarFinder
from astropy.stats import sigma_clipped_stats
from tqdm import tqdm
import pickle

import file_utils


def get_diffs(paths: list) -> tuple:
    diffs, images, times = [], [], []
    for file in paths:
        hdu = fits.open(file)[1]
        images.append(hdu.data)
        times.append(hdu.header['TSTART'])  # 或 DATE-OBS / BJD
    for i in range(len(images) - 1):
        diff = images[i + 1] - images[i]
        diffs.append(diff)
    return diffs, times

def get_diff_sources(diffs: list) -> list:
    diff_sources = []
    for diff in tqdm(diffs, desc='Finding sources in differences'):
        _, _, std = sigma_clipped_stats(diff, sigma=3.0)
        daofind = DAOStarFinder(threshold=5. * std, fwhm=3.0)
        sources = daofind(diff)
        diff_sources.append(sources)
    return diff_sources

if __name__ == '__main__':

    ps = file_utils.get_fits_file_paths('data/')

    ps = ps[25:]  # 先处理一部分数据

    ds, ts = get_diffs(ps)

    np.save('result/little_star/diffs.npy', ds)
    np.save('result/little_star/times.npy', ts)

    diff_s = get_diff_sources(ds)
    with open('result/little_star/diff_sources.pkl', 'wb') as f:
        pickle.dump(diff_s, f)