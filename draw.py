import math
import os
# from datetime import time
import time

import numpy as np
from fitz import fitz

# 1 inch 有72个pt
# 1 inch 有25.4mm
# dpi = 600
# PX2PT = 72 / 600
MM2PT = 72 / 25.4
OUTPUT = './output'
PDF_SAVE = '/pdf'
IMAGE_SAVE = '/image'

FONT_NAME = 'simhei.ttf'
FILE_NAME = "font/" + FONT_NAME
FONT_PATH = os.path.join(os.path.dirname(__file__), FILE_NAME)


def draw_image(data, name=None):
    cid = np.where(data == 255)
    b = np.zeros((data.shape[0], data.shape[1], 5), dtype=np.uint8)
    for i in np.asarray(cid).T:
        b[i[0], i[1], 3] = 255
        b[i[0], i[1], 4] = 255
    b2 = bytearray(b.tobytes())
    pix = fitz.Pixmap(fitz.csCMYK, b.shape[1], b.shape[0], b2, True)
    if name:
        save_image(pix, name)
    return pix


def draw_image_rgb(data, name=None):
    cid = np.where(data == 255)
    b = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
    for i in np.asarray(cid).T:
        b[i[0], i[1], 3] = 255
    b2 = bytearray(b.tobytes())
    pix = fitz.Pixmap(fitz.csRGB, b.shape[1], b.shape[0], b2, True)
    if name:
        save_image(pix, name)
    return pix


def save_image(pix, name):
    path = OUTPUT + IMAGE_SAVE + '/' + time.strftime('%Y-%m-%d')
    if not os.path.exists(path):
        os.makedirs(path)
    pix.save(path + '/' + name)


def set_position(size='A4', cell=(42.7392, 14.2464), row=15, col=4, margin=(20, 15, 20, 15)):
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
    page_u_margin = margin[0] * MM2PT
    page_r_margin = margin[1] * MM2PT
    page_b_margin = margin[2] * MM2PT
    page_l_margin = margin[3] * MM2PT
    # 码点大小
    cell_width = cell[0] * MM2PT
    cell_height = cell[1] * MM2PT
    # 码点间距
    cell_h_margin = ((page_width - page_l_margin - page_r_margin) - (cell_width * col)) / (col + 1)
    cell_v_margin = ((page_height - page_u_margin - page_b_margin) - (cell_height * row)) / (row + 1)
    position = []
    for r in range(row):
        for c in range(col):
            x = page_l_margin + cell_h_margin + (c % col) * (cell_width + cell_h_margin)
            y = page_u_margin + cell_v_margin + r * (cell_height + cell_v_margin)
            x2 = x + cell_width
            y2 = y + cell_height
            position.append((x, y, x2, y2))
    return position


def create_list_pdf(data, position, name, dot_type='bbb', font_name=FONT_NAME, font_path=FONT_PATH):
    """
    绘制一张A4学生码的PDF
    :param dot_type: 码点类型
    :param name: 保存文件名
    :param data: list 学生码列表
    :param position: list 对应的位置列表
    :param font_path: 字体路径
    :param font_name: 字体名称
    """
    doc = fitz.Document()
    # 每页个数
    page_num = len(position)
    # 总页数
    page_total = math.ceil(len(data) / page_num)
    dpi = 300 if dot_type == 'bbb' else 600
    px2pt = 72 / dpi
    images = []
    school_name = data[0]['school_name'] + ' - ' + data[0]['grade_class']
    # 生成PDF页面
    for i in range(page_total):
        doc.new_page()
        start = i * page_num
        end = start + page_num
        images.append(data[start:end])
    # 绘制页面
    for page in doc.pages():
        shape = page.new_shape()
        page.insert_textbox((0, 30, page.rect[2], 40), school_name, fontname=font_name, fontfile=font_path,
                            align=fitz.TEXT_ALIGN_CENTER, color=(0, 0, 0, 1))
        for i in range(len(images[page.number])):
            # rect = fitz.Rect(position[i])
            # page.draw_rect(rect)

            image = images[page.number][i]
            image_mat = image['area']
            x = position[i][0]
            y = position[i][1]
            x2 = x + image_mat.shape[1] * px2pt
            y2 = y + image_mat.shape[0] * px2pt

            min_x, min_y, max_x, max_y = map(str, (image['min_x'], image['min_y'], image['max_x'], image['max_y']))
            text = image['address'] + '-' + min_x + '-' + min_y + '-' + max_x + '-' + max_y
            page.insert_text((position[i][0] + 1, position[i][3] - 1), text, color=(1, 0, 0, 0), fontname=font_name,
                             fontfile=font_path, fontsize=3)
            # 学生名字
            if 'name' in image:
                a = (position[i][3] - y) / 6 * 1.5
                rect = (x, y + a, position[i][2], position[i][3])
                student_name = str(image['name'])
                shape.insert_textbox(rect, student_name, color=(1, 0, 0, 0), fontname=font_name, fontfile=font_path,
                                     align=1, fontsize=8)
                b = (position[i][3] - y) / 6 * 2.8
                rect2 = (x, y + b, position[i][2], position[i][3])
                shape.insert_textbox(rect2, str(image['code']), color=(1, 0, 0, 0), fontname=font_name,
                                     fontfile=font_path, align=1, fontsize=8)
            if 'p' in image:
                shape.insert_textbox(position[i], str(image['p']), color=(0, 0, 1), fontsize=5)
            shape.commit()
            pix = draw_image(image_mat)
            page.insert_image((x, y, x2, y2), pixmap=pix)
        shape.commit()
    path = OUTPUT + PDF_SAVE + '/' + name
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = path + '/list.pdf'
    doc.save(file_path, deflate=True)
    current_path = os.path.abspath(file_path)
    return current_path


def create_multi_pdf(data, position, name, dot_type='bbb', font_name=FONT_NAME, font_path=FONT_PATH):
    doc = fitz.Document()
    page = None
    shape = None
    title_position = None
    dpi = 300 if dot_type == 'bbb' else 600
    px2pt = 72 / dpi
    for i in range(len(data)):
        image = data[i]
        image_mat = image['area']
        pix = draw_image(image_mat)
        if i % 2 == 0:
            page = doc.new_page()
            shape = page.new_shape()
            position_part = position[0]
            title_position = (0, 15, page.rect[2], 30)
        else:
            position_part = position[1]
            title_position = (0, position_part[0][1] - 20, page.rect[2], position_part[0][1] - 5)
        page.insert_textbox(title_position, image['school_name'] + ' - ' + image['grade_class'], fontname=font_name,
                            fontfile=font_path, align=fitz.TEXT_ALIGN_CENTER, color=(0, 0, 0, 1))
        for p in position_part:
            # rect = fitz.Rect(p)
            # page.draw_rect(rect)
            x = p[0]
            y = p[1]
            x2 = x + image_mat.shape[1] * px2pt
            y2 = y + image_mat.shape[0] * px2pt

            min_x, min_y, max_x, max_y = map(str, (image['min_x'], image['min_y'], image['max_x'], image['max_y']))
            text = image['address'] + '-' + min_x + '-' + min_y + '-' + max_x + '-' + max_y
            page.insert_text((p[0] + 1, p[3] - 1), text, color=(1, 0, 0, 0), fontname=font_name, fontfile=font_path,
                             fontsize=3)
            # 学生名字
            if 'name' in image:
                a = (p[3] - y) / 6 * 1.5
                rect = fitz.Rect(x, y + a, p[2], p[3])
                student_name = str(image['name'])
                shape.insert_textbox(rect, student_name, color=(1, 0, 0, 0), fontname=font_name, fontfile=font_path,
                                     align=1, fontsize=8)
                b = (p[3] - y) / 6 * 2.8
                rect2 = (x, y + b, p[2], p[3])
                shape.insert_textbox(rect2, str(image['code']), color=(1, 0, 0, 0), fontname=font_name,
                                     fontfile=font_path, align=1, fontsize=8)
            if 'p' in image:
                shape.insert_textbox(p, str(image['p']), color=(0, 0, 1, 0), fontsize=5)
            shape.commit()

            page.insert_image((x, y, x2, y2), pixmap=pix)
            shape.commit()

    path = OUTPUT + PDF_SAVE + '/' + name
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = path + '/multi.pdf'
    doc.save(file_path, deflate=True)
    current_path = os.path.abspath(file_path)
    return current_path


def create_pdf(data, dot_type='bbb', save_dir=time.strftime('%Y-%m-%d'), pdf_type='list'):
    type_arr = pdf_type.split(',')
    paths = {}
    if 'list' in type_arr:
        position = set_position()
        paths['list'] = create_list_pdf(data, position, save_dir, dot_type=dot_type)
    if 'multi' in type_arr:
        position1 = set_position(row=8, margin=(10, 15, 158, 15))
        position2 = set_position(row=8, margin=(158, 15, 10, 15))
        position = [position1, position2]
        paths['multi'] = create_multi_pdf(data, position, save_dir, dot_type=dot_type)
    return paths
