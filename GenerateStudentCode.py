import argparse
import json

from collect import collect, matrix_unzip
from draw import create_pdf

parser = argparse.ArgumentParser(description='manual to this script')
parser.add_argument("--student-data", type=str, default="[]")  # 学生数据
parser.add_argument("--path", type=str, default="")  # 入库时是铺码pdf的路径，绘制时是生成的PDF路径
parser.add_argument("--type", type=str, default="list")  # list：全部学生在一个列表，multi：同一个学生在一个列表,传多个逗号隔开
parser.add_argument("--target", type=int, default=1)  # 1：入库，2：生成pdf
parser.add_argument("--page-id", type=int, default=0)  # 棒棒帮起始页码
parser.add_argument("--dot-type", type=str, default="bbb")  # 码点类型，bbb=棒棒帮, tsd=拓思德
args = parser.parse_args()

if args.target == 1:
    data = collect(args.path, address_num=args.page_id)
    print(data)
else:
    with open(args.student_data, 'r', encoding='utf-8') as f:
        jsonObject = json.load(f)
    data = [{**item, 'area': matrix_unzip(item['area_char'], dot_type=args.dot_type)} for item in jsonObject]
    pdf_path = create_pdf(data, dot_type=args.dot_type, save_dir=args.path, pdf_type=args.type)
    print(pdf_path)
