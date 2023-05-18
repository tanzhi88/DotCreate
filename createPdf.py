import fitz

# 创建一个空白的 PDF 文档对象
doc = fitz.open()
width = 42.7392
height = 14.2464
width = 100
height = 100
page_num = 10
# 设置 PDF 的大小为 42.7*12.4 厘米
size = (width * 2.835, height * 2.835)  # 转换为点数
# 循环创建 10 页空白的 PDF 页面，并在每页中插入文本
for i in range(page_num):
    page = doc.new_page(width=size[0], height=size[1])
    # 设置文本的位置和字体大小
    where = fitz.Point(50, 100)
    fontsize = 50
    # 插入文本，可以自定义文本内容和样式
    # page.insert_text(where, f"这是第{i+1}页", fontsize=fontsize)
# 设置 PDF 文件的路径和名称
path = "100_100.pdf"
# 将 PDF 文档对象保存到文件中
doc.save(path)
# 关闭 PDF 文档对象
doc.close()

if __name__ == '__main__':
    pass
