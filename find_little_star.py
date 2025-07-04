import numpy as np
from matplotlib import pyplot as plt
import pickle

from tqdm import tqdm


def dfs(index, num, moving_candi, path: list, paths: list):
    """
    深度优先搜索，寻找所有可能的轨迹路径
    :param index: 第几帧的候选移动目标
    :param num: 当前帧的候选移动目标索引
    :param moving_candi: 所有帧的候选移动目标列表
    :param path: 搜索到的当前路径
    :param paths: 存放最终找到的所有路径
    :return:
    """
    if index >= len(moving_candi) - 1:
        if len(path) >= 10:
            paths.append(path.copy())
        return

    cur_x, cur_y, cur_peak, cur_flux = path[-1][0], path[-1][1], path[-1][2], path[-1][3]

    visited[index].add(num)  # 标记当前点为已访问

    has_next = False
    for i, s in enumerate(moving_candi[index + 1]):
        next_x, next_y, next_peak, next_flux = s['xcentroid'], s['ycentroid'], s['peak'], s['flux']

        dx = next_x - cur_x
        dy = next_y - cur_y
        dist = np.hypot(dx, dy)

        if dist < 5.0: # and abs(cur_peak - next_peak) / cur_peak < 0.5 and abs(cur_flux - next_flux) / cur_flux < 0.5:
            # 认为 s 是同一个目标的下一个点
            path.append([next_x, next_y, next_peak, next_flux])
            dfs(index + 1, i, moving_candi, path, paths)
            path.pop()  # 回溯
            has_next = True
    if not has_next:
        # 如果没有下一个点，记录当前路径
        if len(path) >= 10:
            paths.append(path.copy())

if __name__ == '__main__':

    ds = np.load('result/little_star/diffs.npy', allow_pickle=True)
    times = np.load('result/little_star/times.npy', allow_pickle=True)
    print(f"总共有 {len(ds)} 帧的差分图像")

    # diff_sources = get_diff_sources(ds)
    # diff_sources = np.load('result/little_star/diff_sources.npy', allow_pickle=True)
    with open('result/little_star/diff_sources.pkl', 'rb') as f:
        diff_sources = pickle.load(f)
    print(f"总共找到 {len(diff_sources)} 帧的候选移动目标")

    paths = []
    # 对每一帧的候选移动目标进行深度优先搜索，寻找所有可能的轨迹路径
    visited = [set() for _ in range(len(diff_sources))]
    for i, diff_source in enumerate(tqdm(diff_sources, desc='Processing frames')):
        for j, point in enumerate(diff_source):
            sx, sy, spe, flu = point['xcentroid'], point['ycentroid'], point['peak'], point['flux']
            if j not in visited[i]: # 避免用一个已经访问过的点开始新的路径
                dfs(0, j, diff_sources, [[sx, sy, spe, flu]], paths)

    # 现在 paths 包含了所有可能的轨迹路径
    print(f"找到 {len(paths)} 条可能的轨迹路径")

    paths.sort(key=lambda p: len(p), reverse=True)  # 按路径长度排序，最长的在前面

    for i, path in enumerate(tqdm(paths[:1000], desc='Processing paths')):
        # 提取轨迹信息
        x = [p[0] for p in path]
        y = [p[1] for p in path]
        t = [t for t in times]  # times 是 FITS 头部中提取的时间信息

        # 像素速度（可视化用）
        vx = (x[-1] - x[0]) / (t[-1] - t[0])
        vy = (y[-1] - y[0]) / (t[-1] - t[0])
        v_pix = np.hypot(vx, vy)
        print(f"像素速度：{v_pix:.2f} px/day")

        # 绘制轨并保存到文件
        plt.plot(x, y, 'o-')
        plt.title(f"move_pixel_coord-{i} v:{v_pix:.2f}px/day len:{len(path)}")
        plt.xlabel("X (pixel)")
        plt.ylabel("Y (pixel)")
        plt.gca().invert_yaxis()
        plt.savefig(f'result/little_star/fig/move_pixel_coord_{i}_len:{len(path)}.png')
        plt.close()

        f = [p[3] for p in path]
        plt.plot(f, marker='o')
        plt.title(f"flux_change-{i}-len：{len(path)}")
        plt.xlabel("Time (30min)")
        plt.ylabel("Flux")
        plt.savefig(f'result/little_star/fig2/flux_change_{i}-len：{len(path)}.png')
        plt.close()

