from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import UsageRecord, Sneaker
from app.database import get_db
from sqlalchemy import func
from pyecharts.charts import Line, Bar
from pyecharts import options as opts


def add_usage_records(records: list[dict]):
    try:
        with get_db() as db:
            usage_objects = [UsageRecord(
                sneaker_id=r["sneaker_id"],
                date=datetime.strptime(r["date"], "%Y-%m-%d").date(),
                activity=r["activity"],
                location=r["location"],
                duration=int(r["duration"]) if r["duration"] else 0,
                notes=r["notes"]) for r in records]

            db.add_all(usage_objects)
            db.commit()

    except Exception as e:
        print("[错误] 保存使用记录失败：", e)
        db.rollback()


def get_daily_usage_records():
    """
    返回过去90天内，每日穿鞋记录的数量（即每日使用次数统计）
    格式: List[{"date": "2025-06-01", "count": 3}]
    """
    with get_db() as db:
        start = datetime.today().date() - timedelta(days=90)
        end = datetime.today().date() + timedelta(days=1)

        results = (
            db.query(
                UsageRecord.date,
                func.count(UsageRecord.id).label("count")
            )
            .filter(UsageRecord.date >= start)
            .filter(UsageRecord.date <= end)
            .filter(UsageRecord.activity.in_([
                "穿着打球", "穿着通勤", "穿着休闲", "穿着旅游"
            ]))
            .group_by(UsageRecord.date)
            .order_by(UsageRecord.date)
            .all()
        )

        return [{"date": r.date.strftime("%Y-%m-%d"), "count": r.count} for r in results]


def get_sneaker_usage_counts():
    """
    返回过去90天每双球鞋穿着的总次数，按次数排序
    返回: List[Tuple[str, int]]
    """
    with get_db() as db:
        start = datetime.today().date() - timedelta(days=90)

        results = (
            db.query(Sneaker.name, UsageRecord)
            .join(Sneaker, Sneaker.id == UsageRecord.sneaker_id)
            .filter(UsageRecord.date >= start)
            .filter(UsageRecord.activity.in_([
                "穿着打球", "穿着通勤", "穿着休闲", "穿着旅游"
            ]))
            .all()
        )

        counter = {}
        for sneaker_name, _ in results:
            counter[sneaker_name] = counter.get(sneaker_name, 0) + 1

        return sorted(counter.items(), key=lambda x: x[1], reverse=True)


def get_usage_frequency():
    """统计各球鞋使用频率（近3个月）"""
    today = datetime.today().date()
    three_months_ago = today - timedelta(days=90)

    with get_db() as db:
        results = (
            db.query(UsageRecord.sneaker_id, func.count(UsageRecord.id).label("count"))
            .filter(UsageRecord.date >= three_months_ago.strftime('%Y-%m-%d'))
            .group_by(UsageRecord.sneaker_id)
            .all()
        )
        sneaker_map = {s.id: s.name for s in db.query(Sneaker).all()}
        usage_freq = [{"name": sneaker_map.get(sid, "未知"), "count": count} for sid, count in results]
        print("[调试] 使用频率排行：", usage_freq)
        return usage_freq


def render_daily_usage_chart(data):
    """生成每日穿鞋趋势图（Line）"""
    if not data:
        return Line().set_global_opts(title_opts=opts.TitleOpts(title="近三月穿鞋趋势"))

    dates = [d["date"] for d in data]
    counts = [d["count"] for d in data]

    line = (
        Line()
        .add_xaxis(dates)
        .add_yaxis("穿鞋次数", counts)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="近三月穿鞋趋势"),
            xaxis_opts=opts.AxisOpts(type_="category"),
            yaxis_opts=opts.AxisOpts(name="次数"),
        )
    )
    return line


def render_usage_frequency_chart(data):
    """生成穿鞋频次排行图（Bar）"""
    if not data:
        return Bar().set_global_opts(title_opts=opts.TitleOpts(title="穿鞋频率排行"))

    names = [d["name"] for d in data]
    counts = [d["count"] for d in data]

    bar = (
        Bar()
        .add_xaxis(names)
        .add_yaxis("穿着次数", counts)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="穿鞋频率排行"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30)),
            yaxis_opts=opts.AxisOpts(name="次数"),
        )
    )
    return bar


def get_usage_records_by_date(date_str: str):
    """
    获取某一天的所有穿鞋记录（含球鞋名称）
    输入: "2025-06-01"
    返回: List[{"sneaker": "AJ1 Chicago", "activity": "穿着通勤"}]
    """
    with get_db() as db:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        results = (
            db.query(UsageRecord, Sneaker)
            .join(Sneaker, Sneaker.id == UsageRecord.sneaker_id)
            .filter(UsageRecord.date == target_date)
            .all()
        )

        return [
            {
                "sneaker": r.Sneaker.name,
                "activity": r.UsageRecord.activity,
                "location": r.UsageRecord.location,
                "duration": r.UsageRecord.duration,
                "notes": r.UsageRecord.notes,
            }
            for r in results
        ]


def delete_records_by_date(date_str):
    from app.database import get_db
    with get_db() as db:
        deleted = db.query(UsageRecord).filter(
            UsageRecord.date == datetime.strptime(date_str, "%Y-%m-%d").date()).delete()
        db.commit()
        return deleted > 0  # 返回是否真的删除了数据
