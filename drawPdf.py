import json
import math
import os
import re
import time

import numpy as np
import cv2
import fitz

down = np.zeros((7, 7), dtype=int)
down[2:4, 1:3] = 255
up = np.zeros((7, 7), dtype=int)
up[:2, 1:3] = 255
left = np.zeros((7, 7), dtype=int)
left[1:3, :2] = 255
right = np.zeros((7, 7), dtype=int)
right[1:3, 2:4] = 255
b2h = {"0000": "0", "0001": "1", "0010": "2", "0011": "3", "0100": "4", "0101": "5", "0110": "6", "0111": "7",
       "1000": "8", "1001": "9", "1010": "A", "1011": "B", "1100": "C", "1101": "D", "1110": "E", "1111": "F"}


def discern(grain):
    """
    识别一个最小单位，返回二进制数据
    :return: bin
    """
    if np.all(grain[0:2, 1:3] == 255):
        return '00'
    if np.all(grain[1:3, 2:] == 255):
        return '01'
    if np.all(grain[2:, 1:3] == 255):
        return '10'
    if np.all(grain[1:3, :2] == 255):
        return '11'
    return 'err'


def array_to_bin(grain):
    if np.all(grain == up):
        return '00'
    if np.all(grain == right):
        return '01'
    if np.all(grain == down):
        return '10'
    if np.all(grain == left):
        return '11'


def bin_to_array(grain):
    if grain == '00':
        return up
    if grain == '01':
        return right
    if grain == '10':
        return down
    if grain == '11':
        return left


def unzip_grain(grain):
    grain_array = np.zeros((7, 7), dtype=int)
    if grain == '00':
        grain_array[0:2, 1:3] = 255
    if grain == '01':
        grain_array[1:3, 2:4] = 255
    if grain == '10':
        grain_array[2:4, 1:3] = 255
    if grain == '11':
        grain_array[1:3, :2] = 255
    return grain_array


def draw_image(data, name=None):
    cid = np.where(data == 255)
    # b = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
    # for i in np.asarray(cid).T:
    #     b[i[0], i[1], 3] = 255
    # b2 = bytearray(b.tobytes())
    # pix = fitz.Pixmap(fitz.csRGB, b.shape[1], b.shape[0], b2, True)
    b = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
    for i in np.asarray(cid).T:
        b[i[0], i[1], 3] = 255
    b2 = bytearray(b.tobytes())
    pix = fitz.Pixmap(fitz.csCMYK, b.shape[1], b.shape[0], b2, False)
    path = './output/image/' + time.strftime('%Y-%m-%d')
    if not os.path.exists(path):
        os.makedirs(path)
    if name:
        pix.save(path + '/' + name)
    return pix


def fill_mat(data, multiple=0, modulo=0, axis=1):
    """
    填充码点
    :param data: 码点数据
    :param multiple: 需要填充的面积是码点面积的倍数
    :param modulo: 要填充部份达不到码点面积倍数的余数
    :param axis:
    :return:
    """
    new_data = data
    if multiple:
        for i in range(multiple):
            new_data = np.concatenate((new_data, data), axis=axis)
    if modulo:
        data = data[:modulo] if axis == 0 else data[:, :modulo]
        new_data = np.concatenate((new_data, data), axis=axis)
    return new_data


def unzip_img(data, area_num=24):
    """
    解压码点文件
    1. 转成二进制形式
    2. 将每个二进制形式的识别单元转成二维数组，并加上空白区
    3. 组合合并识别单元成为识别区
    4. 把解压好的数组装在列表里返回
    :param area_num:
    :param data: list 压缩的图片列表
    :return: list
    """
    for i in range(len(data)):
        area_char = data[i]['area_char']
        bin_str = bin(int(area_char, 16))[2:].zfill(len(area_char) * 4)
        grain_str_list = re.findall(r'.{2}', bin_str)
        grain_list = []
        grain_row = []
        for grain_i in range(len(grain_str_list)):
            grain_arr = bin_to_array(grain_str_list[grain_i])
            grain_row.append(grain_arr)
            # 每个识别单元有6个最小单位组成
            if (grain_i + 1) % (6 * area_num) == 0:
                row = np.hstack(grain_row)
                grain_row = []
                grain_list.append(row)
        data[i]['area'] = np.vstack(grain_list)
    return data


class Draw:
    # 最细粒度，由4X4个像素组成，加3个空白
    grain = 7
    # 一个识别单位
    cell = grain * 6
    # 一个识别单位的像素宽高
    cell_size = (45, 15)
    img = []
    address = ''
    doc = object
    page = object
    ir = object
    position = []
    dpi = 600
    # 1 inch 有72个pt
    pt = 72
    # 1 inch 有25.4mm
    mm = 25.4
    mm_to_px = dpi / mm
    mm_to_pt = pt / mm
    pt_to_px = dpi / pt
    pt_to_mm = mm / pt
    px_to_pt = pt / dpi
    px_to_mm = mm / dpi
    output = './output'
    pdf_save = '/pdf'

    def stock(self, dot_image, address):
        self.img = dot_image
        self.address = address
        self._trim_data()
        area_list = self._slice_data()
        return area_list

    def _trim_data(self):
        """
        去除周边空白
        """
        c_start = self._trim_data_get_index()
        c_end = self._trim_data_get_index('r')
        r_start = self._trim_data_get_index('u')
        r_end = self._trim_data_get_index('d')
        self.img = self.img[r_start:r_end + 1, c_start:c_end + 1]

    def _trim_data_get_index(self, direction='l'):
        """
        从一个方向进行遍历，返回第一行或列不为0的index
        :param direction: 方向 l：从左到右 r: 从右到左 u: 从上到下 d: 从下到上
        :return: 行号或列号
        """
        i = -1
        p = 1 if (direction == 'l' or direction == 'u') else -1
        if direction == 'r':
            i = self.img.shape[1]
        if direction == 'd':
            i = self.img.shape[0]
        g = True
        while g:
            i = i + p
            if direction == 'u' or direction == 'd':
                data = self.img[i]
            else:
                data = self.img[:, i]
            g = np.all(data == 0)
        return i

    def _slice_data(self, area=(24,8), margin=2):
        """
        分割数据
        .   一个最小的识别单位为 45 X 45 个像素矩阵组成，其中，黑点区域有 6 X 6 个
        .   一个黑点区域由 4 X 4 个像素组成，真正的黑点只占其中 2 X 2 个像素，其余部份均为透明点
        .   每两个黑点区域相隔着三个透明点，上面左右均三个
        .   1. 先计算一个区域长宽分别能装几个最小识别单位
        .   2. 用最小识别单位重复填充区域，组成一个新矩陈
        .   3. 将新矩陈转成 rgba 颜色矩陈
        .   4. 建立像素图，用颜色矩陈绘制，插入页面
        :param area: 按几个识别单元来切割，可以是一个int值，可以是一个元组，如果是一个元组则分别代表长宽
        :param margin: 每个切割区域的间隔数，以识别单元为单位
        :return: list 切割区域列表
        """
        # 一个分割区域由一个识别区加一个隔离区组成
        area_width = area[0] * self.cell + margin * self.cell
        area_height = area[1] * self.cell + margin * self.cell
        # 计算一共能分割成几行几列
        h = math.floor(self.img.shape[1] / area_width)
        v = math.floor(self.img.shape[0] / area_height)
        # 将原图进行截断，保证能分割均匀
        self.img = self.img[:v * area_height, :h * area_width]
        # 先进行纵向切割
        h_array = np.hsplit(self.img, h)
        area_list = []
        for col in range(len(h_array)):
            v_array = np.vsplit(h_array[col], v)
            # if col == 0:
            #     draw_image(h_array[0], 'col-0.png')
            for row in range(len(v_array)):
                # 11200为A3尺寸PDF的最大x轴码点坐标值，9797
                min_x = math.floor(((col * (margin + area[0]) * 42) + (margin * 42) + 2) * 11200 / 9797)
                max_x = math.floor(((col + 1) * (margin + area[0]) * 42 + 2) * 11200 / 9797)
                min_y = math.floor(((row * (margin + area[1]) * 42) + (margin * 42) + 1) * 7920 / 6934)
                max_y = math.floor(((row + 1) * (margin + area[1]) * 42 + 1) * 7920 / 6934)
                position = {'address': self.address, 'min_x': min_x, 'max_x': max_x, 'min_y': min_y, 'max_y': max_y}
                area_mat = v_array[row][margin * self.cell:, margin * self.cell:]
                position['area_char'] = self._slice_grain2(area_mat)
                position['p'] = str(col) + '-' + str(row)
                # if col == 0 and row == 0:
                #     draw_image(area_mat, str(col) + '-' + str(row) + '.png')
                #     self._create_test_pdf(area_mat, position, str(col) + '-' + str(row))
                area_list.append(position)
        return area_list

    def _slice_cell(self, area):
        """
        将一个区域分割成多个识别单位
        :param area: 区域
        :return: char
        """
        char_list = []
        h_array = np.hsplit(area, area.shape[1] / self.cell)
        for col in range(len(h_array)):
            v_array = np.vsplit(h_array[col], area.shape[0] / self.cell)
            for row in range(len(v_array)):
                cell = v_array[row][:self.cell, :self.cell]
                char_list.append(self._slice_grain(cell))
        return ','.join(char_list)

    def _slice_grain(self, cell):
        """
        分割数据
        :param cell: 要分割的数据
        :return: char
        """
        char_list = []
        char_str = ''
        h_array = np.hsplit(cell, cell.shape[1] / self.grain)
        for col in range(len(h_array)):
            v_array = np.vsplit(h_array[col], cell.shape[0] / self.grain)
            for row in range(len(v_array)):
                grain = v_array[row][:3, :3]
                char_str += discern(grain)
                if len(char_str) == 4:
                    char_list.append(b2h[char_str])
                    char_str = ''
        return ''.join(char_list)

    def _slice_grain2(self, area):
        char_list = []
        char_str = ''
        h_array = np.vsplit(area, area.shape[0] / self.grain)
        for col in range(len(h_array)):
            v_array = np.hsplit(h_array[col], area.shape[1] / self.grain)
            for row in range(len(v_array)):
                char_str += array_to_bin(v_array[row])
                if len(char_str) == 4:
                    char_list.append(b2h[char_str])
                    char_str = ''
        return ''.join(char_list)

    def _create_test_pdf(self, data, position, name):
        width = data.shape[0] * self.px_to_pt
        height = data.shape[1] * self.px_to_pt
        pdf = fitz.open()
        page = pdf.new_page(width=width, height=height)
        shape = page.new_shape()
        min_x = str(position['min_x'])
        min_y = str(position['min_y'])
        max_x = str(position['max_x'])
        max_y = str(position['max_y'])
        address = position['address'] + '-' + min_x + '-' + min_y + '-' + max_x + '-' + max_y
        shape.insert_text((1, height - 1), address, color=(0, 0, 0), fontsize=3)
        # shape.insert_textbox((width / 2, height / 2), name, color=(0, 0, 1), fontsize=8)
        shape.commit()
        pix = draw_image(data)
        page.insert_image((0, 0, data.shape[1] * self.px_to_pt, data.shape[0] * self.px_to_pt), pixmap=pix)
        path = self.output + self.pdf_save + '/' + time.strftime('%Y-%m-%d')
        if not os.path.exists(path):
            os.makedirs(path)
        pdf.save(path + '/' + name + '.pdf')

    def set_position(self, size='A4', cell=(42.7392, 14.2464), row=11, col=3, margin=(5, 5, 5, 5)):
        """
        计算每个位置
        :param size: 页面大小
        :param cell: tuple 每个码点的大小
        :param row: int 排成几排
        :param col: int 排成几列
        :param margin: tuple 页面边距
        :return: list 一个页面的位置列表
        """
        # 页面大小
        size_rect = fitz.paper_size(size)
        page_width = size_rect[0]
        page_height = size_rect[1]
        # 页边距
        page_u_margin = margin[0] * self.mm_to_pt
        page_r_margin = margin[1] * self.mm_to_pt
        page_b_margin = margin[2] * self.mm_to_pt
        page_l_margin = margin[3] * self.mm_to_pt
        # 码点大小
        self.cell_size = cell
        cell_width = cell[0] * self.mm_to_pt
        cell_height = cell[1] * self.mm_to_pt
        # 码点间距
        cell_h_margin = ((page_width - page_l_margin - page_r_margin) - (cell_width * col)) / (col + 1)
        cell_v_margin = ((page_height - page_u_margin - page_b_margin) - (cell_height * row)) / (row + 1)
        position = []
        for r in range(row):
            for c in range(col):
                x = cell_h_margin + (c % col) * (cell_width + cell_h_margin)
                y = cell_v_margin + r * (cell_height + cell_v_margin)
                x2 = x + cell_width
                y2 = y + cell_height
                position.append((x, y, x2, y2))
        return position

    def create_list_pdf(self, data, position, name):
        """
        绘制一张A4学生码的PDF
        :param name: 保存文件名
        :param data: list 学生码列表
        :param position: list 对应的位置列表
        """
        doc = fitz.Document()
        # 每页个数
        page_num = len(position)
        # 总页数
        page_total = math.ceil(len(data) / page_num)
        images = []
        # 生成PDF页面
        for i in range(page_total):
            doc.new_page()
            start = i * page_num
            end = start + page_num
            images.append(data[start:end])
        # 绘制页面
        for page in doc.pages():
            shape = page.new_shape()
            for i in range(len(images[page.number])):
                # rect = fitz.Rect(position[i])
                # page.draw_rect(rect)

                image = images[page.number][i]
                image_mat = image['area']
                x = position[i][0]
                y = position[i][1]
                x2 = x + image_mat.shape[1] * self.px_to_pt
                y2 = y + image_mat.shape[0] * self.px_to_pt

                pix = draw_image(image_mat)
                page.insert_image((x, y, x2, y2), pixmap=pix)
                min_x = str(image['min_x'])
                min_y = str(image['min_y'])
                max_x = str(image['max_x'])
                max_y = str(image['max_y'])
                text = image['address'] + '-' + min_x + '-' + min_y + '-' + max_x + '-' + max_y
                page.insert_text((position[i][0] + 1, position[i][3] - 1), text, 3)
                # 学生名字
                if 'name' in image:
                    a = (position[i][3] - y) / 6 * 1.5
                    rect = (x, y + a, position[i][2], position[i][3])
                    student_name = str(image['name'])
                    shape.insert_textbox(rect, student_name, color=(0, 0, 0), fontname='china-s', align=1, fontsize=8)
                    b = (position[i][3] - y) / 6 * 2.8
                    rect2 = (x, y + b, position[i][2], position[i][3])
                    shape.insert_textbox(rect2, str(image['code']), color=(0, 0, 0), align=1, fontsize=8)
                if 'p' in image:
                    shape.insert_textbox(position[i], str(image['p']), color=(0, 0, 1), fontsize=5)
            shape.commit()
        path = self.output + self.pdf_save + '/' + name
        if not os.path.exists(path):
            os.makedirs(path)
        doc.save(path + '/list.pdf', deflate=True)

    def create_single_pdf(self, student_data, save_dir, width=42.7392, height=14.2464):
        width = width * self.mm_to_pt
        height = height * self.mm_to_pt
        pdf = fitz.open()
        page = pdf.new_page(width=width, height=height)
        shape = page.new_shape()

        min_x = str(student_data['min_x'])
        min_y = str(student_data['min_y'])
        max_x = str(student_data['max_x'])
        max_y = str(student_data['max_y'])

        mat = student_data['area']
        pix = draw_image(mat)
        page.insert_image((0, 0, mat.shape[1] * self.px_to_pt, mat.shape[0] * self.px_to_pt), pixmap=pix)
        shape.insert_text(
            (1, height - 1),
            student_data['address'] + '-' + min_x + '-' + min_y + '-' + max_x + '-' + max_y,
            fontsize=3,
        )
        name = ''
        code = 1234567
        if 'name' in student_data:
            name = student_data['name']
            code = student_data['code']
        if 'p' in student_data:
            name = student_data['p']
        # 插入文字
        box_rect = fitz.Rect(0, height / 6 * 1.3, width, height)
        shape.insert_textbox(
            box_rect,
            str(name),
            fontname='china-s',
            align=1
        )
        shape.insert_textbox(
            (0, height / 6 * 3, width, height),
            str(code),
            align=1,
            fontsize=8
        )
        shape.commit()
        path = self.output + self.pdf_save + '/' + save_dir
        if not os.path.exists(path):
            os.makedirs(path)
        pdf.save(path + '/' + name + '.pdf', deflate=True)


def create_pdf(data, save_dir=time.strftime('%Y-%m-%d'), t='list,single'):
    """
    生成PDF
    :param data: list 数据列表
    :param save_dir: str 保存PDF的文件夹名称
    :param t: str 要生成的类型,有两种类型，一种是 list, 一种是single， 可以选多个，用逗号隔开
    """
    draw = Draw()
    data = unzip_img(data)
    type_arr = t.split(',')
    if 'single' in type_arr:
        for i in range(len(data)):
            draw.create_single_pdf(data[i], save_dir)
    if 'list' in type_arr:
        position = draw.set_position()
        draw.create_list_pdf(data, position, save_dir)


def import_pdf(file):
    """
    将码点入库
    :param file:
    :return:
    """
    draw = Draw()
    pdf = fitz.open(file)
    for page in pdf:
        imageList = page.getImageList()
        text = page.get_text()
        address = text.split(' ')[0]
        for imageInfo in imageList:
            pix = fitz.Pixmap(pdf, imageInfo[0])
            data = pix.tobytes(output="png")
            image_array = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
            # draw_image(img, '1.png')
            areas = draw.stock(img, address)
            path = './output/json'
            if not os.path.exists(path):
                os.makedirs(path)
            with open(path + "/" + address + ".json", "w", encoding='utf-8') as f:
                json.dump(areas, f, ensure_ascii=False, sort_keys=True, indent=4)


if __name__ == '__main__':
    # import_pdf('./pdf/A3.pdf')
    with open('output/json/1713.537.32.77.json', 'r', encoding='utf-8') as f:
        data_list = json.load(f)
    create_pdf(data_list[:10])
