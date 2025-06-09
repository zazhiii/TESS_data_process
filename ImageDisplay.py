import matplotlib.pyplot as plt
import file_utils
import numpy as np

# 文件列表
folder = "data/"
fits_file_names = file_utils.get_fits_file_names(folder)

# 提取图像数据
# FILE_NUM = 146 # 选择要处理的文件编号
FILE_NUM = 49  # 选择要处理的文件编号
image_data, hdr = file_utils.read_image_data(folder + fits_file_names[FILE_NUM])

# clip 过滤像素值
image_data1, image_data2, image_data3 = file_utils.clip_image_data(image_data)

plt.imshow(image_data1)
plt.show()

# 手动调试固定值
plt.figure(figsize=(12, 6))
plt.subplot(2, 3, 1)
plt.imshow(image_data1)
plt.title('fixed clipping')

plt.subplot(2, 3, 2)
plt.imshow(image_data2)
plt.title('percentile clipping')

# 基于图像统计量
plt.subplot(2, 3, 3)
plt.title('statistics clipping')
plt.imshow(image_data3)

plt.subplot(2, 3, 4)
plt.hist(image_data1.flatten(), bins=100)

plt.subplot(2, 3, 5)
plt.hist(image_data2.flatten(), bins=100)

plt.subplot(2, 3, 6)
plt.hist(image_data3.flatten(), bins=100)

plt.show()
plt.close()

