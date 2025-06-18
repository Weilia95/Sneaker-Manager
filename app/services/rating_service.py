# app/services/rating_service.py


def calculate_total_score(ratings):
    """
    取最新一次评分，计算所有整数型字段的平均分，保留一位小数
    """
    if not ratings:
        return None
    latest = ratings[-1]
    # 收集所有整数分数字段
    nums = [
        latest.cushion,
        latest.traction,
        latest.torsion,
        latest.durability,
        latest.wrap,
        latest.anti_roll,
        latest.weight,
        latest.comfort
    ]
    # 过滤 None
    nums = [n for n in nums if isinstance(n, (int, float))]
    if not nums:
        return None
    avg = sum(nums) / len(nums)
    return round(avg, 1)


def sort_by_total_score_desc(sneakers):
    def get_key(sneaker):
        score = calculate_total_score(sneaker.ratings)
        # 有评分的用负数保证降序，无评分的用正无穷排到最后
        return -score if score is not None else float('inf')

    return sorted(sneakers, key=get_key)


def sort_by_total_score_asc(sneakers):
    def get_key(sneaker):
        score = calculate_total_score(sneaker.ratings)
        # 有评分的正常升序，无评分的排到最后
        return score if score is not None else float('inf')

    return sorted(sneakers, key=get_key)


def sort_by_dimension(sneakers, dimension, reverse=False):
    """
    按指定维度排序（取最新一次评分）
    """
    def get_dimension_value(sneaker):
        if not sneaker.ratings:
            return 0
        return getattr(sneaker.ratings[-1], dimension)

    return sorted(sneakers, key=get_dimension_value, reverse=reverse)