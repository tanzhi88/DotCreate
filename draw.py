import io
import math
import os
# from datetime import time
import time

import numpy as np
from fitz import fitz
from reportlab.lib.units import mm
from barcode import EAN13
from barcode.writer import ImageWriter

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


def generate_code(data):
    """
    生成条码
    :param data:
    :return:
    """
    # 创建一个不包含数字的Writer实例
    writer = ImageWriter()

    # 使用数据生成条形码图像
    ean = EAN13(data, writer)

    # 获取生成的PIL Image对象
    options = {
        'write_text': None,  # 是否显示文字
        # 'module_width': 0.2,  # 线条宽度
        'module_height': 2,  # 图片高度
        'font_size': 8,  # 显示文字的大小
        'text_distance': 0,  # 文字与条码距离
        'quiet_zone': 1,  # 两边空白大小
        'margin_top': 0.1,  # 上部空白大小
        'margin_bottom': 0  # 下部空白大小
    }
    barcode_image = ean.render(writer_options=options)

    # 将 PIL.Image 转换为 bytes 数据
    image_bytes = io.BytesIO()
    barcode_image.save(image_bytes, format='PNG')  # 保存为 PNG 格式
    image_data = image_bytes.getvalue()

    return fitz.Pixmap(image_data)


def get_position(width=50, height=20, num_rows=13, num_cols=4, col_padding=2, row_padding=2):
    """
    获取位置信息
    :param width: 每个区域的宽度
    :param height: 每个区域的高度
    :param num_rows: 排成几排
    :param num_cols: 排成几列
    :param col_padding: 列宽
    :param row_padding: 行宽
    :return: list
    """
    page_width, page_height = 210, 297
    # 计算总间隔
    total_col_spacing = (num_cols - 1) * col_padding
    total_row_spacing = (num_rows - 1) * row_padding
    # 计算所有矩形高宽
    total_rect_width = num_cols * width + total_col_spacing
    total_rect_height = num_rows * height + total_row_spacing
    start_x = (page_width - total_rect_width) / 2
    start_y = (page_height - total_rect_height) / 2

    position = []
    for row in range(num_rows):
        for col in range(num_cols):
            # 计算当前矩形的位置
            x = start_x + col * (width + col_padding)
            y = start_y + row * (height + row_padding)
            x2 = x + width
            y2 = y + height
            position.append((x * mm, y * mm, x2 * mm, y2 * mm))
    return position


def get_ele_rect(rect, width, height, h_offset):
    """
    获取每个要绘制的元素位置
    主要通过与每个矩形位置计算出来
    :param rect:
    :param width:
    :param height:
    :param h_offset:
    :return:
    """
    x0 = (rect.width - width) / 2 + rect.x0
    y0 = rect.y0 + h_offset
    x1 = x0 + width
    y1 = y0 + height
    return fitz.Rect(x0, y0, x1, y1)


def create_list_pdf(data, position, save_dir):
    """
    绘制一张A4学生码的PDF
    :param save_dir: 保存文件名
    :param data: list 学生码列表
    :param position: list 对应的位置列表
    """
    doc = fitz.Document()
    # 每页个数
    page_num = len(position)
    # 在学生列表前加入学校班级
    data.insert(0, {'school_area': True, 'school_name': data})
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
        for i in range(len(images[page.number])):
            image = images[page.number][i]
            if 'school_area' in image and len(images) >= i + 1:
                student_data = images[page.number][i + 1]
                school_name = student_data['school_name'] if 'school_name' in student_data else '学校名称'
                class_name = student_data['grade_class'] if 'grade_class' in student_data else '班级名称'
                draw_school(page, position[i], school_name, class_name)
            else:
                dot_pixmap = draw_image(data=image['area'])
                name = image['name'] if 'name' in image else '姓名'
                code = str(image['code']) if 'code' in image else '123456789012'
                draw_ele(page, position[i], dot_pixmap, name, code)

    path = OUTPUT + PDF_SAVE + '/' + save_dir
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = path + '/list.pdf'
    doc.save(file_path, deflate=True)
    current_path = os.path.abspath(file_path)
    return current_path


def create_multi_pdf(data, position, save_dir):
    """绘制单个学生多张码"""
    doc = fitz.Document()
    page = None
    part_len = int(len(position) / 2)
    for i in range(len(data)):
        image = data[i]
        dot_pixmap = draw_image(image['area'])
        name = image['name'] if 'name' in image else '姓名'
        code = str(image['code']) if 'code' in image else '123456789012'
        if i % 2 == 0:
            page = doc.new_page()
            position_part = position[:part_len]
        else:
            position_part = position[part_len:]

        for index, p in enumerate(position_part):
            if index == 0:
                school_name = image['school_name'] if 'school_name' in image else '学校名称'
                class_name = image['grade_class'] if 'grade_class' in image else '班级名称'
                draw_school(page, p, school_name, class_name)
            else:
                draw_ele(page, p, dot_pixmap, name, code)

    path = OUTPUT + PDF_SAVE + '/' + save_dir
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = path + '/multi.pdf'
    doc.save(file_path, deflate=True)
    current_path = os.path.abspath(file_path)
    return current_path


def draw_ele(page, position, dot_pixmap, name, code, font_name=FONT_NAME, font_path=FONT_PATH):
    """
    绘制具体的元素
    :param page: page对像
    :param position: 要绘制的位置
    :param dot_pixmap: 码点图片
    :param name: 学生名字
    :param code: 学生唯一码
    :param font_name: 字体名称
    :param font_path: 字体路经
    :return: 无
    """
    img_width, img_height = 42.7392 * mm, 14.2464 * mm
    code_width, code_height = 42.5 * mm, 2 * mm
    rect = fitz.Rect(position)
    # 条形码
    code_pixmap = generate_code(code)
    page.insert_image(get_ele_rect(rect, code_width, code_height, 4.5), pixmap=code_pixmap)
    # 码点
    dot_rect = get_ele_rect(rect, img_width, img_height, 10.5)
    page.insert_image(dot_rect, pixmap=dot_pixmap)
    # 学生名字
    if name:
        page.insert_textbox(dot_rect, f"{name}({code})", fontname=font_name, fontfile=font_path, fontsize=8)


def draw_school(page, position, school_name, class_name, font_name=FONT_NAME, font_path=FONT_PATH):
    """
    绘制学校信息
    """
    school_position = (position[0] + 2, position[1] + 14, position[2] - 2, position[1] + 36)
    school_rect = fitz.Rect(school_position)
    class_rect = fitz.Rect(school_rect.bl, school_rect.x1, school_rect.y1 + 12)
    page.insert_textbox(school_rect, school_name, fontname=font_name, fontfile=font_path, fontsize=8, align=1)
    page.insert_textbox(class_rect, class_name, fontname=font_name, fontfile=font_path, fontsize=8, align=1)


def create_pdf(data, save_dir=time.strftime('%Y-%m-%d'), pdf_type='list'):
    type_arr = pdf_type.split(',')
    path = ''
    position = get_position()
    if 'list' in type_arr:
        path = create_list_pdf(data, position, save_dir)
    if 'multi' in type_arr:
        path = create_multi_pdf(data, position, save_dir)
    return path
