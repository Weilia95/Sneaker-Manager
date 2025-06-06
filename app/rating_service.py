# app/services/rating_service.py


def calculate_total_score(ratings):
    """
    计算最新一次评分的平均分（所有维度权重相同）
    """
    if not ratings:
        return None

    latest_rating = ratings[-1]  # 只取最后一次评分
    total = (
        latest_rating.cushion * 0.25 +
        latest_rating.traction * 0.25 +
        latest_rating.durability * 0.25 +
        latest_rating.torsion * 0.25
    )
    return round(total, 1)


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