import numpy as np

# 矩阵的阶数
N = 5


def get_matrix():
    """
    创建一个5x5的随机整数矩阵
    :return:
    """

    return np.random.randint(1, 5, size=(N, N))


def tri(matrix, method="low"):
    """
    保留矩阵的上三角或下三角
    :param matrix:
    :param method:
    :return:
    """
    x = [
        [0, 0, 0, 1, 1, 0, 0, 1, 0, 1],
        [1, 0, 0, 0, 1, 0, 0, 1, 0, 1],
        [0, 1, 0, 1, 1, 0, 0, 1, 0, 1],
        [0, 1, 1, 0, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0, 0, 1, 0, 1],
        [0, 0, 1, 1, 1, 0, 1, 0, 0, 1],
        [0, 1, 0, 1, 0, 0, 0, 1, 0, 1],
        [0, 0, 1, 1, 1, 0, 0, 1, 0, 1],
        [0, 0, 0, 1, 1, 0, 0, 1, 0, 1],
        [0, 1, 1, 0, 1, 0, 0, 1, 0, 1]]
    # return x
    return np.tril(matrix) if method == "low" else np.triu(matrix)


def diag(matrix):
    """
    生成对称矩阵
    :param matrix:
    :return:
    """
    return matrix + matrix.T - np.diag(matrix.diagonal())


def init_list():
    """
    根据矩阵维度生成一个一维数组存储对称矩阵数据
    :return:
    """
    return [0] * (int((N + 1) * N / 2))


def get_index(x, y):
    """
    根据x,y获取对应列表中的索引, 计算公式为: x>=y时 x(x+1)/2 + y, x<y时 y(y+1)/2 + x
    :param x:
    :param y:
    :return:
    """
    if x >= y:
        return x * (x + 1) // 2 + y
    return y * (y + 1) // 2 + x


def save_to_list(index_array, r_list, r_mt):
    """
    将数据存储到一维数组中
    :param index_array:
    :param r_list:
    :param r_mt:
    :return:
    """
    for index in range(len(r_list)):
        x, y = index_array[1][index], index_array[0][index]
        r_list[get_index(x, y)] = r_mt[y][x]
    return r_list


def list_to_matrix(r_list):
    """
    将数组还原为对称矩阵
    :param r_list:
    :return:
    """
    new_matrix = np.zeros((N, N), dtype=int)
    new_matrix_index = np.where(new_matrix == 0)
    for index in range(len(new_matrix_index[0])):
        x, y = new_matrix_index[1][index], new_matrix_index[0][index]
        new_matrix[y, x] = r_list[get_index(x, y)]
    return new_matrix


if __name__ == '__main__':
    mt = get_matrix()
    print(mt)
    low_mt = tri(mt)
    diag_mt = diag(low_mt)
    print("生成的对称矩阵为：\n%s" % diag_mt)

    low_diag_mt = tri(diag_mt)
    print("保留下三角的矩阵数据: \n%s" % low_diag_mt)

    no_zero_index = np.nonzero(low_diag_mt)

    i_list = init_list()
    print("根据维度初始化的数组长度为: \n%s" % len(i_list))

    res_list = save_to_list(no_zero_index, i_list, low_diag_mt)
    print("存储后的数组为:\n%s" % res_list)

    res_matrix = list_to_matrix(res_list)
    print("还原后的对称矩阵为: \n %s" % res_matrix)