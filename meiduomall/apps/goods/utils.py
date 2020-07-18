


def get_breadcrumb(cat3):
    """
    面包屑导航
    :param cat3: 三级分类
    :return: 面包屑导航
    """
    # 查询二级和一级分类
    cat2 = cat3.parent
    cat1 = cat2.parent

    # 封装面包屑导航名字
    breadcrumb = {
        'cat1': cat1.name,
        'cat2': cat2.name,
        'cat3': cat3.name
    }

    return breadcrumb