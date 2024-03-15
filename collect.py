import math
import re

import numpy as np
from fitz import fitz


lt = np.array([[255, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])  # [0, 0]
rt = np.array([[0, 255, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])  # [0, 1]
lb = np.array([[0, 0, 0, 0], [255, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])  # [1, 0]
rb = np.array([[0, 0, 0, 0], [0, 255, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])  # [1, 1]

# -------- 600-9 -----------#
# 中间
matrix_000 = np.zeros((8, 8), dtype=int)
matrix_000[1:4, 1:4] = 255

# 左上
matrix_001 = np.zeros((8, 8), dtype=int)
matrix_001[0:3, 0:3] = 255

# 左下
matrix_010 = np.zeros((8, 8), dtype=int)
matrix_010[2:5, 0:3] = 255

# 右上
matrix_011 = np.zeros((8, 8), dtype=int)
matrix_011[0:3, 2:5] = 255

# 右下
matrix_100 = np.zeros((8, 8), dtype=int)
matrix_100[2:5, 2:5] = 255


def array_to_bin(grain):
    if np.array_equal(grain, lt):
        return '00'
    elif np.array_equal(grain, rt):
        return '01'
    elif np.array_equal(grain, lb):
        return '10'
    elif np.array_equal(grain, rb):
        return '11'
    elif np.array_equal(grain, matrix_000):
        return '000'
    elif np.array_equal(grain, matrix_001):
        return '001'
    elif np.array_equal(grain, matrix_011):
        return '011'
    elif np.array_equal(grain, matrix_010):
        return '010'
    elif np.array_equal(grain, matrix_100):
        return '100'
    else:
        raise ValueError('Unknown grain input: {}'.format(grain))


def bin_to_array(grain):
    mappings = {
        '00': lt,
        '01': rt,
        '10': lb,
        '11': rb,
        '000': matrix_000,
        '001': matrix_001,
        '011': matrix_011,
        '010': matrix_010,
        '100': matrix_100
    }
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

    # 用非 0 下标重新分割矩阵
    return matrix[rows.min(): rows.max() + 1, cols.min(): cols.max() + 1]


def matrix_zip(matrix, area, ppi, size, width, height):
    """
    压缩信息
    将图片列表转换为二进制数据，压缩二进制数据，将压缩后的数据转换为字符串返回
    【600-9】
    600表示图表的ppi为600
    9表示黑点占9个点（3*3）
    加上白点共占5*5， 加上间隔共占8*8，也就是说，一个基本单元占8*8的空间
    【300-1】
    300表示图表的ppi为300
    1表示黑点占1个点（1*1）
    加上白点共占2*2， 加上间隔共占4*4，也就是说，一个基本单元占4*4的空间
    把黑点及周边的白点及间隔算一个基本单元，按单元大小进行分割，最终将每个单元进行转换成二进制
    :param matrix: 图片矩阵
    :param area: 最小单元的大小
    :param size: 码点大小类型
    :param ppi: 图表像素密度
    :param width: 要切割的图像宽度
    :param height: 要切割的图像高度
    :return: 字符串
    """
    # 先按指定大小切分图片
    n_w = math.floor(width / 25.4 * ppi)
    n_h = math.floor(height / 25.4 * ppi)
    matrix = matrix[:n_h, :n_w]
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
    bin_str = ''.join(string_list)
    string = hex(int(bin_str, 2))[2:]
    hex_string = f'{str(matrix.shape[0])}*{str(matrix.shape[1])}|{str(len(bin_str))}|{string}'
    if ppi == 600 and size == 9:
        hex_string = f'{str(ppi)}-{str(size)}|{hex_string}'
    return hex_string


def collect(pdf, address_num=0, ppi=600, size=9, width=42.7392, height=14.2464):
    """
    采集信息
    读取PDF文件，从PDF中获取每页的图片，组成一个列表
    :param address_num: 码点起始ID
    :param pdf: pdf文件路径
    :param size: 码点大小类型
    :param ppi: 图表像素密度
    :param width: 要切割的图像宽度
    :param height: 要切割的图像高度
    :return: str
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
        data = np.frombuffer(bytes(pix.samples), dtype=np.uint8)
        o_height, o_width = pix.height, pix.width
        img = np.reshape(data, (o_height, o_width))
        address = '21.' + str(address_num)
        address_num += 1
        if ppi == 600 and size == 9:
            area = 8
            img_matrix = np.copy(img[2:-1, 2:-1])
        else:
            area = 4
            img_matrix = np.copy(img[1:-1, 1:-1])
        hex_str = matrix_zip(img_matrix, area=area, ppi=ppi, size=size, width=width, height=height)
        json_arr.append({
                     'address': address,
                     'min_x': 0,
                     'max_x': 100,
                     'min_y': 0,
                     'max_y': 100,
                     'area_char': hex_str
                        })
        pix = None  # 释放 Pixmap 对象的内存空间

    # 关闭 PDF 文件
    doc.close()
    return json_arr


def matrix_unzip(area_char):
    """
    将字符串转成矩阵
    :param area_char: 字符串
    :return: 矩阵
    """
    # 分离字符串并获取图像尺寸和数据
    strings = area_char.split("|")
    if strings[0] == '600-9':
        shape_str = strings[1]
        str_len = strings[2]
        hex_str = strings[3]
        bin_len = 3
        area_num = 8
    else:
        shape_str = strings[0]
        str_len = strings[1]
        hex_str = strings[2]
        bin_len = 2
        area_num = 4
    rows, cols = map(int, shape_str.split("*"))
    # 将32位的十六进制数据转化为二进制字符串
    # bin_str = bin(int(hex_str, 16))[2:].zfill(len(hex_str) * 4)
    bin_str = format(int(hex_str, 16), '0' + str(int(str_len)) + 'b')
    str_list = re.findall(fr'.{{{bin_len}}}', bin_str)
    max_col = cols / area_num
    block_list = []
    block_row = []
    for i in range(len(str_list)):
        block_arr = bin_to_array(str_list[i])
        block_row.append(block_arr)
        # 达到一行时换行
        if (i + 1) % max_col == 0:
            row = np.hstack(block_row)
            block_row = []
            block_list.append(row)
    return np.vstack(block_list)
