import math
import re

import cv2
import numpy as np
from fitz import fitz

import draw
from draw import save_image

lt = np.array([[255, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])  # [0, 0]
rt = np.array([[0, 255, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])  # [0, 1]
lb = np.array([[0, 0, 0, 0], [255, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])  # [1, 0]
rb = np.array([[0, 0, 0, 0], [0, 255, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])  # [1, 1]
down = np.zeros((7, 7), dtype=int)
down[2:4, 1:3] = 255
up = np.zeros((7, 7), dtype=int)
up[:2, 1:3] = 255
left = np.zeros((7, 7), dtype=int)
left[1:3, :2] = 255
right = np.zeros((7, 7), dtype=int)
right[1:3, 2:4] = 255


def array_to_bin(grain):
    if np.array_equal(grain, up) or np.array_equal(grain, lt):
        return '00'
    elif np.array_equal(grain, right) or np.array_equal(grain, rt):
        return '01'
    elif np.array_equal(grain, down) or np.array_equal(grain, lb):
        return '10'
    elif np.array_equal(grain, left) or np.array_equal(grain, rb):
        return '11'
    else:
        raise ValueError('Unknown grain input: {}'.format(grain))


def bin_to_array(grain, t='bbb'):
    bbb = {'00': lt, '01': rt, '10': lb, '11': rb}
    tsd = {'00': up, '01': right, '10': down, '11': left}
    mappings = bbb if t == 'bbb' else tsd
    return mappings.get(grain)


def trim_zeros(matrix):
    """
    去除矩阵周边所有为0的行和列
    :param matrix:
    :return:
    """
    # 找到布尔矩阵中所有为True的行的下标
    rows = np.where(np.sum(matrix != 0, axis=1))[0]
    cols = np.where(np.sum(matrix != 0, axis=0))[0]

    # 用非0下标重新分割矩阵
    return matrix[rows.min(): rows.max() + 1, cols.min(): cols.max() + 1]


def slice_data(img, address, area=(24, 8), margin=2):
    """
    分割数据
    .   一个最小的识别单位为 45 X 45 个像素矩阵组成，其中，黑点区域有 6 X 6 个
    .   一个黑点区域由 4 X 4 个像素组成，真正的黑点只占其中 2 X 2 个像素，其余部份均为透明点
    .   每两个黑点区域相隔着三个透明点，上面左右均三个
    .   1. 先计算一个区域长宽分别能装几个最小识别单位
    .   2. 用最小识别单位重复填充区域，组成一个新矩陈
    .   3. 将新矩陈转成 rgba 颜色矩陈
    .   4. 建立像素图，用颜色矩陈绘制，插入页面
    :param address:
    :param img:
    :param area: 按几个识别单元来切割，可以是一个int值，可以是一个元组，如果是一个元组则分别代表长宽
    :param margin: 每个切割区域的间隔数，以识别单元为单位
    :return: list 切割区域列表
    """
    cell = 7 * 6
    # 一个分割区域由一个识别区加一个隔离区组成
    area_width = area[0] * cell + margin * cell
    area_height = area[1] * cell + margin * cell
    # 计算一共能分割成几行几列
    h = math.floor(img.shape[1] / area_width)
    v = math.floor(img.shape[0] / area_height)
    # 将原图进行截断，保证能分割均匀
    img = img[:v * area_height, :h * area_width]
    # 先进行纵向切割
    h_array = np.hsplit(img, h)
    area_list = []
    for col in range(len(h_array)):
        v_array = np.vsplit(h_array[col], v)
        for row in range(len(v_array)):
            # 11200为A3尺寸PDF的最大x轴码点坐标值，9797
            min_x = math.floor(((col * (margin + area[0]) * 42) + (margin * 42) + 2) * 11200 / 9797)
            max_x = math.floor(((col + 1) * (margin + area[0]) * 42 + 2) * 11200 / 9797)
            min_y = math.floor(((row * (margin + area[1]) * 42) + (margin * 42) + 1) * 7920 / 6934)
            max_y = math.floor(((row + 1) * (margin + area[1]) * 42 + 1) * 7920 / 6934)
            position = {'address': address, 'min_x': min_x, 'max_x': max_x, 'min_y': min_y, 'max_y': max_y}
            area_mat = v_array[row][margin * cell:, margin * cell:]
            position['area_char'] = matrix_zip(area_mat, 7)
            position['p'] = str(col) + '-' + str(row)
            area_list.append(position)
    return area_list


def matrix_zip(matrix, area=4):
    """
    压缩信息
    将图片列表转换为二进制数据，压缩二进制数据，将压缩后的数据转换为字符串返回
    :param matrix: 图片矩阵
    :param area: 最小单元的大小
    :return: 字符串
    """
    # 计算一共能分割成几行几列
    h = matrix.shape[1] // area  # 需要分割成几行
    v = matrix.shape[0] // area  # 需要分割成几列
    # 将原图进行截断，保证能分割均匀
    matrix = matrix[:v * area, :h * area]
    # 先按行切割矩阵
    blocks = np.split(matrix, v, axis=0)
    # 再按列切割每个子矩阵
    blocks = [np.split(block, h, axis=1) for block in blocks]
    # 把所有的小块合并成一个数组
    blocks = np.concatenate(blocks)
    string_list = []
    # 循环读取每个小块
    for block in blocks:
        string_list.append(array_to_bin(block))
    string = hex(int(''.join(string_list), 2))[2:]
    return string


def collect(pdf, address_num=0):
    """
    采集信息
    读取PDF文件，从PDF中获取每页的图片，组成一个列表
    :param address_num: 码点起始ID
    :param pdf: pdf文件路径
    :return:
    """
    # 打开 PDF 文件
    doc = fitz.open(pdf)
    json_arr = []
    # 遍历每个页面
    for page in doc:
        # 获取当前页面中的所有图像
        images = page.get_images()
        # 获取图像像素信息
        xref = images[0][0]
        pix = fitz.Pixmap(doc, xref)
        samples = bytes(pix.samples)
        data = np.frombuffer(samples, dtype=np.uint8)
        height, width = pix.height, pix.width
        img = np.reshape(data, (height, width))
        if address_num:
            img_matrix = np.copy(img[1:-1, 1:-1])
            n_w = math.floor(42.7392 / 25.4 * 300)
            n_h = math.floor(14.2464 / 25.4 * 300)
            img_matrix = img_matrix[:n_h, :n_w]
            address = '21.' + str(address_num)
            address_num += 1
            area = 4
            # 计算一共能分割成几行几列
            h = img_matrix.shape[1] // area  # 需要分割成几行
            v = img_matrix.shape[0] // area  # 需要分割成几列
            # 将原图进行截断，保证能分割均匀
            matrix = img_matrix[:v * area, :h * area]
            shape = matrix.shape
            string = matrix_zip(matrix)
            hex_str = str(shape[0]) + '*' + str(shape[1]) + '|' + str(len(string)) + '|' + string
            json_arr.append({
                'address': address,
                'min_x': 0,
                'max_x': 100,
                'min_y': 0,
                'max_y': 100,
                'area_char': hex_str
            })
        else:
            new_img = np.copy(trim_zeros(img))
            text = page.get_text()
            address = text.split(' ')[0]
            json_arr += slice_data(new_img, address)
        pix = None  # 释放 Pixmap 对象的内存空间

    # 关闭 PDF 文件
    doc.close()
    return json_arr


def matrix_unzip(area_char, dot_type='bbb'):
    """
    将字符串转成矩阵
    :param area_char: 字符串
    :param dot_type: 码点类型
    :return: 矩阵
    """
    if dot_type == 'bbb':
        # 分离字符串并获取图像尺寸和数据
        shape_str, data_len_str, hex_str = area_char.split("|")
        rows, cols = map(int, shape_str.split("*"))
        data_len = int(data_len_str)
        # 将32位的十六进制数据转化为二进制字符串
        bin_str = bin(int(hex_str, 16))[2:].zfill(data_len)
        max_col = cols / 4
    else:
        bin_str = bin(int(area_char, 16))[2:].zfill(len(area_char) * 4)
        max_col = 6 * 24  # 每个识别单元有6个最小单位组成
    str_list = re.findall(r'.{2}', bin_str)
    block_list = []
    block_row = []
    for i in range(len(str_list)):
        block_arr = bin_to_array(str_list[i], t=dot_type)
        block_row.append(block_arr)
        # 达到一行时换行
        if (i + 1) % max_col == 0:
            row = np.hstack(block_row)
            block_row = []
            block_list.append(row)
    return np.vstack(block_list)
