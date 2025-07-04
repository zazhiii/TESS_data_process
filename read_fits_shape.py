from astropy.io import fits
import sys
import os

# 默认 FITS 文件路径
FITS_PATH = 'data/tess2018319112938-s0005-1-4-0125-s_ffic.fits'

def print_fits_shapes(fits_path):
    if not os.path.exists(fits_path):
        print(f"文件不存在: {fits_path}")
        return
    with fits.open(fits_path) as hdul:
        for i, hdu in enumerate(hdul):
            shape = hdu.data.shape if hdu.data is not None else None
            print(f"HDU {i}: shape = {shape}")

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else FITS_PATH
    print_fits_shapes(path)

