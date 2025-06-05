
# FITS 文件数据结构解析
你运行 `hdulist.info()` 得到的信息如下：

```
No.    Name      Ver    Type      Cards   Dimensions   Format
  0  PRIMARY       1 PrimaryHDU      30   ()      
  1  CAMERA.CCD 1.4 cal    1 ImageHDU       183   (2136, 2078)   float32   
  2  CAMERA.CCD 1.4 uncert    1 ImageHDU       183   (2136, 2078)   float32 
```

下面是逐项解释这些内容的含义：

---

### 第0个 HDU：`PRIMARY`

* **Name**: `PRIMARY`
* **Type**: `PrimaryHDU`
* **Cards**: 30（即 header 中有30项键值对）
* **Dimensions**: `()` 表示这个 HDU 中没有图像数据（空）
* **Format**: 无

**说明**：
主头单元（Primary HDU）通常是 FITS 文件的第一个部分，可能包含关键的元信息（比如观测时间、目标编号、仪器信息等），但本例中它没有图像数据。

---

### 第1个 HDU：`CAMERA.CCD 1.4 cal`

* **Name**: `CAMERA.CCD 1.4 cal`
* **Type**: `ImageHDU`
* **Cards**: 183（即 header 中有183项键值对）
* **Dimensions**: `(2136, 2078)`，图像是 2136 列 × 2078 行的二维数组
* **Format**: `float32`，图像像素为 32位浮点数

**说明**：
这是经过\*\*校准（calibrated）\*\*后的图像数据，也就是你要提取目标亮度信息的主要数据。

---

### 第2个 HDU：`CAMERA.CCD 1.4 uncert`

* **Name**: `CAMERA.CCD 1.4 uncert`
* **Type**: `ImageHDU`
* **Cards**: 183
* **Dimensions**: `(2136, 2078)`
* **Format**: `float32`

**说明**：
这是每个像素的**不确定度（uncertainty）图像**，即每个像素值的不确定性估计，可用于后续误差分析或滤波。

---

### 实际用途总结：

| HDU索引 | 内容说明            | 是否使用           |
| ----- | --------------- | -------------- |
| 0     | 主头，包含元信息        | ✅（读取头信息）       |
| 1     | 校准图像数据（主要图像）    | ✅（主处理数据）       |
| 2     | 不确定度图像（每个像素的误差） | ✅（可选，做误差估计时使用） |

---

### Python 示例：读取图像与头信息

```python
from astropy.io import fits

# 打开 FITS 文件
hdulist = fits.open("your_file.fits")

# 图像数据
image_data = hdulist[1].data  # 使用第1个HDU
uncertainty_data = hdulist[2].data  # 第2个HDU，如果需要误差分析

# 图像维度
print("图像维度：", image_data.shape)

# 图像头信息
header = hdulist[1].header
print(header['DATE-OBS'])  # 例如打印观测日期
```

---

# 图像数据裁剪的作用
这行代码：

```python
image_data = np.clip(image_data, a_min=0, a_max=400)
```

的作用是**将图像数据中的像素值限制在 0 到 400 的范围之间**，超出这个范围的值会被截断（裁剪）。

---

### 🔍 分步解释：

* `image_data`：二维数组，代表图像中每个像素的亮度值（float 或 int）。
* `np.clip(array, a_min, a_max)`：NumPy 的裁剪函数。

  * 若某个像素值 `< a_min`（即小于0），则设为 `0`；
  * 若某个像素值 `> a_max`（即大于400），则设为 `400`；
  * 其余值保持不变。

---

### 🎯 为什么要这样做？

1. **去除异常值或噪声**：

   * TESS 图像中可能有高亮“坏像素”或负值（背景扣除后），会干扰图像可视化或星点检测。

2. **提高图像可视化效果**：

   * 用 `imshow` 显示图像时，极端亮度值会导致大部分区域过暗或过亮；
   * 限制在 0-400 可让亮度对比更清晰、星点更明显。

3. **避免后续算法（如找星、拟合）出错**：

   * 某些算法对极端值敏感，可能导致误检或收敛失败。

---

### 🧠 举个例子：

假设某个图像像素值如下：

```python
image_data = np.array([[10, -5, 420],
                       [30, 100, 390]])
```

执行 `np.clip(image_data, 0, 400)` 后变为：

```python
[[ 10   0 400]
 [ 30 100 390]]
```

---

如需我进一步解释为何选取 **400** 作为最大值，或怎么选择合适的上下限，也可以继续问。

# 如何选择图像裁剪上下限

选择图像像素值的裁剪上下限（`a_min` 和 `a_max`），主要是为了平衡以下两个目标：

* **突出天体信号**（如恒星）；
* **抑制极端值对显示和算法的干扰**。

以下是几种常见且实用的方法来**自动或手动选择合适的上下限**：

---

### ✅ 方法一：使用分位数（percentile）自动确定上下限

```python
vmin = np.percentile(image_data, 1)   # 下限设为第1百分位
vmax = np.percentile(image_data, 99)  # 上限设为第99百分位
image_data = np.clip(image_data, vmin, vmax)
```

* **优点**：鲁棒、自动适应不同图像；
* **适用场景**：大部分像素是背景，只有少数亮点（如星星）；
* **解释**：

  * 下限设第1百分位，可滤掉背景噪声或负值；
  * 上限设第99百分位，可排除极亮异常像素（如坏点）。

---

### ✅ 方法二：基于图像统计量（如均值 + n×标准差）

```python
from astropy.stats import sigma_clipped_stats

mean, median, std = sigma_clipped_stats(image_data, sigma=3.0)

vmin = median - 1 * std
vmax = median + 5 * std
image_data = np.clip(image_data, vmin, vmax)
```

* **适用性强**，可滤除背景偏差或热像素；
* `vmax = median + 5*std`：保留大多数天体但滤掉极端亮点；
* `vmin = median - 1*std`：避免背景低值过暗或为负。

---

### ✅ 方法三：手动调试固定值（仅适用于少量图像）

* 如果你已经看过图像直方图，可以手动设置：

```python
plt.hist(image_data.flatten(), bins=100, log=True)
```

看图像像素值的分布，大致决定：

```python
image_data = np.clip(image_data, a_min=0, a_max=400)
```

* 通常 `a_max` 在 300–500 范围内都能较好地显示亮星。

---

### 📌 总结建议

| 方法   | 优点       | 缺点         | 适用情况         |
| ---- | -------- | ---------- | ------------ |
| 分位数法 | 自适应、鲁棒   | 非线性结构可能受影响 | 推荐用于图像显示与预处理 |
| 统计量法 | 可控性强、抗噪声 | 需要计算背景统计量  | 自动化处理与找星分析   |
| 手动设定 | 快速、直观    | 不通用        | 仅用于调试或固定数据集  |


# 识别目标星的像素范围（使用 FWHM）

### 1.4 识别目标星的像素范围（使用 FWHM）

在处理 TESS 的全幅图像时，确定目标天体的像素覆盖范围是提取精确光变曲线的关键步骤。由于每个星点在图像上并不局限于单个像素，而是呈现为一个具有扩展的亮斑，通常接近二维高斯分布，因此我们可通过测量其 **全宽半高（FWHM, Full Width at Half Maximum）** 来估算星点的尺寸及采样区域。

#### （1）FWHM的含义与作用

FWHM 表示星点光强分布的宽度，是从光强峰值的一半处所对应的直径。对于接近高斯形状的星点，它能反映出其在图像中的扩散程度。通过测量目标星的 FWHM，可以据此定义提取光变曲线时所使用的像素区域，一般选择：

$$
\text{采样半径} = 1.5 \sim 2 \times \text{FWHM}
$$

这样可以最大程度地覆盖目标星的光通量，同时减少背景与邻近星的干扰。

#### （2）基于 DAOStarFinder 识别星点和 FWHM

我们使用 `photutils` 库中的 `DAOStarFinder` 方法自动检测图像中的星点，并测量每个星点的位置、峰值亮度和 FWHM。处理流程如下：

```python
from photutils.detection import DAOStarFinder
from astropy.stats import sigma_clipped_stats

# 获取图像背景信息
mean, median, std = sigma_clipped_stats(image_data, sigma=3.0)

# 检测星点，设置阈值为背景的5倍标准差
daofind = DAOStarFinder(fwhm=3.0, threshold=5. * std)
sources = daofind(image_data - median)

# 提取前几个星点信息
for i in range(5):
    x = sources['xcentroid'][i]
    y = sources['ycentroid'][i]
    fwhm = sources['fwhm'][i]
    print(f"星点{i+1}：位置=({x:.2f}, {y:.2f}), FWHM={fwhm:.2f}")
```

输出示例：

```
星点1：位置=(1052.33, 1048.89), FWHM=3.21
星点2：位置=(987.12, 1023.45), FWHM=2.95
...
```

#### （3）基于FWHM构建光变曲线采样区域

确定目标星的中心像素和FWHM后，可以围绕其中心建立一个固定半径的圆形 aperture 区域（如 `r = 2 × FWHM`），将该区域内的像素亮度加总（或进行背景校正后加总），即可作为该目标在该时刻的亮度。

在后续处理每一张图像时，只需重复该过程并记录该区域的亮度，即可获得完整的光变曲线。

> 若图像中存在多个星点重叠，或背景不均匀，可采用 PSF 拟合方法进一步提取精确亮度，但在本实习中使用 FWHM + aperture photometry 即可满足大部分提取任务。

# 星点数据结构解析

| 字段名           | 含义                                                              |
| ------------- | --------------------------------------------------------------- |
| `id`          | 星源的编号，从1开始递增，主要用于识别索引                                           |
| `xcentroid`   | 星点在图像上的 **X方向重心坐标**（浮点数，亚像素精度）                                  |
| `ycentroid`   | 星点在图像上的 **Y方向重心坐标**                                             |
| `sharpness`   | 尖锐度指标：描述目标相比于周围像素背景的“突兀程度”<br>值越高，说明星点越像一个集中亮源；越低则可能是背景噪声或扩展源   |
| `roundness1`  | 圆度指标1：描述星点是否在两个轴上对称（主用于去除条状伪源）                                  |
| `roundness2`  | 圆度指标2：更复杂的圆度测量方法（适合光轴偏移图像）                                      |
| `npix`        | 被认为属于该星点的像素数量                                                   |
| `peak`        | 星点中最亮像素的值（峰值亮度）                                                 |
| `flux`        | 星点的总亮度（净光通量），通常是最关键的物理量之一                                       |
| `mag`         | 根据 `flux` 推算出的“仪器星等”或相对星等<br>（通常是 `-2.5 * log10(flux)`，未校正绝对零点） |
| `daofind_mag` | 与 `mag` 一致，可能是从 `DAOStarFinder` 输出中单独保留的冗余列（你可以比较一下两列是否相同）      |

这是一个非常关键、非常好的问题。因为你是通过**图像中星星的位置**来提取光变曲线，而 TESS 的 **256 张 FFI 图像中，恒星的位置可能会有轻微漂移**（由于望远镜抖动、姿态调整等）。

---


# 如何选择参考图像来识别星星位置

应该**从其中一张质量最好、背景干净、目标明显的一张图像中识别星星的位置**，**通常选用第50张或中间的一张**，然后在其基础上建立目标星的初始像素位置。

---

## 🔍 原因详解：

### 为什么不能用每张图都去找星星？

* 星点识别是**比较耗时**的操作；
* 不同图像中星星可能有细微漂移，你会识别出不同位置；
* 这会导致你提取的光变曲线**不一致、带入背景误差或相邻星干扰**。

---

## ✅ 推荐做法（专业工作流）：

### 第一步：选择一张“参考帧”作为主图（比如第50张）

```python
fits_files = sorted(glob.glob('your_path/*.fits'))
reference_file = fits_files[49]  # 第50张，索引为49
```

### 第二步：在这张图像上提取星点位置（使用 DAOStarFinder）

```python
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils import DAOStarFinder

# 打开参考帧
hdul = fits.open(reference_file)
image_data = hdul[0].data
hdul.close()

# 估算背景
mean, median, std = sigma_clipped_stats(image_data, sigma=3.0)
daofind = DAOStarFinder(fwhm=3.0, threshold=5.*std)
sources = daofind(image_data - median)

# 得到你感兴趣的源的坐标
x = sources['xcentroid'][0]  # 或手动选取某一颗
y = sources['ycentroid'][0]
```

### 第三步：在之后所有图像中用这个固定坐标提取相同区域的光变曲线（比如以 `x,y` 为中心 5×5 区域）

---

## 💡 高级建议：漂移校正（配准）

如果你发现目标星亮度“忽明忽暗但没有物理周期性”，可能是因为图像漂移了，你可以：

* 使用 `image_registration` 或 `photutils` 的 `Centroid2D` 来做配准；
* 或者在每一张图中用 `DAOStarFinder` 找目标星最接近的位置（但计算量较大）。

---

## ✅ 总结流程建议：

| 步骤     | 内容                             |
| ------ | ------------------------------ |
| 1.     | 从中间一张图（如第50张）中提取所有星点位置（参考帧）    |
| 2.     | 选定你的目标星（最亮的，或指定位置的）坐标 `(x, y)` |
| 3.     | 在所有图像中围绕此坐标固定窗口提取亮度值，形成光变曲线    |
| 4.（可选） | 若需要高精度，可进行漂移校正或星点再定位           |


