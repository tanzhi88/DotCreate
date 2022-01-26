import fitz
import os
import math
import requests


class Compose:
    dir = './pdf'
    output = './output'
    files = []
    # mm转换pt参数
    c = 0.3527
    # 10mm间距
    space = 0
    h_space = 15 / c
    x = 0
    y = h_space
    doc = object
    page = object
    urls = []

    def __init__(self, dir='./pdf', urls=[]):
        self.dir = dir
        self._get_file()
        self.doc = fitz.open()
        self.page = self.doc.new_page()
        self.urls = urls

    def _get_file(self):
        """获取文件夹下所有文件"""
        for root, dir, files in os.walk(self.dir):
            self.files = files

    def _set_rect(self):
        """设定每个pdf位置"""

        for file in self.files:
            str = file.split('.')
            if str[-1] == 'pdf':
                # 把每个文件读取进来
                rec = fitz.open(self.dir + '/' + file)
                p = rec.load_page(0)
                # 如果没有设置过间隔则进行设置
                if self.space == 0:
                    self._set_space(p.rect.width)

                # 设置一个矩形框，用于粘贴pdf
                r = fitz.Rect(self.x, self.y, p.rect.width + self.x, p.rect.height + self.y)
                self.page.show_pdf_page(r, rec, 0, rotate=0)
                self._w(file, self.x, self.y)
                self._set_next_position(p.rect.width, p.rect.height)

    # def _set_next_position(self, width, height):
    #     """设置下一个PDF的位置"""
    #     self.x = self.x + width + self.space
    #
    #     # 如果一排已经排不下，则换下一行
    #     if (self.page.rect.width - self.x) < (width + self.space):
    #         self.y += height + self.h_space
    #         self.x = self.space
    #
    #     # 如果一页排不下了，则新建立一页
    #     if (self.page.rect.height - self.y) < (height + self.space):
    #         self.page = self.doc.new_page()
    #         self.x = self.space
    #         self.y = self.h_space

    def _w(self, text, x, y):
        """写入文字"""
        tw = fitz.TextWriter(self.page.rect)
        tw.append((x, y), text, fontsize=5, small_caps=True)
        tw.write_text(self.page)

    def save(self, name='haha.pdf'):
        file = self.output + '/' + name
        self._set_rect()
        self.doc.save(file)
        self.doc.close()

    def _set_space(self, width):
        """设置X的间隔"""
        g = math.floor(self.page.rect.width / width)
        y = self.page.rect.width - (width * (g - 1))
        self.space = y / g
        self.x = self.space

    def down_pdf(self):
        for url in self.urls:
            str_file = url.split('/')
            name = str_file[-1]
            print(name)
            r = requests.get(url, stream=True)
            with open(self.dir + '/' + name, 'wb') as f:
                f.write(r.content)


if __name__ == '__main__':
    urls = ['https://pen.zwres.com/pdf/dev/student/1713.537.32.77/1-1713.537.32.77-10-10-1100-360.pdf']
    c = Compose(urls=urls)
    c.save()
