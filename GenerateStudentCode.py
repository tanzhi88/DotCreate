import argparse
import json

from collect import collect
from draw import create_pdf

parser = argparse.ArgumentParser(description='manual to this script')
parser.add_argument("--student-data", type=str, default="[]")  # 学生数据
parser.add_argument("--path", type=str, default="output")  # 入库时是铺码pdf的路径，绘制时是生成的PDF路径
parser.add_argument("--type", type=str, default="list")  # list：全部学生在一个列表，multi：同一个学生在一个列表,传多个逗号隔开
parser.add_argument("--target", type=int, default=1)  # 1：入库，2：生成pdf
parser.add_argument("--page-id", type=int, default=0)  # 棒棒帮起始页码
parser.add_argument("--dot-type", type=int, default="bbb")  # 码点类型，bbb=棒棒帮, tsd=拓思德
args = parser.parse_args()

if args.target == 1:
    data = collect(args.path, address_num=args.page_id)
else:
    with open(args.student_data, 'r', encoding='utf-8') as f:
        jsonObject = json.load(f)
    create_pdf(jsonObject, dot_type=args.dot_type, save_dir=args.path, pdf_type=args.type)
