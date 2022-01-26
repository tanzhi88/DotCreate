import fitz, os
import cv2

doc = fitz.open('./105X105_dot.pdf')

img_count = 0
for page in doc:
    imageList = page.getImageList()
    text = page.get_text()
    print(text)
    for imageInfo in imageList:
        pix = fitz.Pixmap(doc, imageInfo[0])
        print(pix)
        # p = os.path.join("./image/test/t_{}.png".format(img_count))
        # print(p)
        pix.save("./105X105.png")
        img_count += 1

if __name__ == '__main__':
    print('PyCharm')
