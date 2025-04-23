"""insert_5_default_records

Revision ID: f47ac10b58cc
Revises: 9dde57c6fd53
Create Date: 2025-04-19 20:30:00.000000
"""
import uuid
import random
import string
from datetime import datetime, timezone, date
from typing import Sequence, Union

from alembic import op
from sqlalchemy.orm import Session

from app.models import (
    Member,
    SportType,
    Activity,
    ExerciseRecord,
    SportPreference,
    UserReview,
    ActivityJoin,
    ActivityReview,
    TimeOption,
)

# revision identifiers, used by Alembic.
revision: str = "f47ac10b58cc"
down_revision: Union[str, None] = "9dde57c6fd53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    while True:
        pw = ''.join(random.choices(chars, k=length))
        if (any(c.islower() for c in pw) and
            any(c.isupper() for c in pw) and
            any(c.isdigit() for c in pw)):
            return pw

def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    now = datetime.now(timezone.utc)

    members = []
    cities = ["臺北市", "新北市", "桃園市", "臺中市", "高雄市"]
    areas = ["中正區", "板橋區", "平鎮區", "西區", "苓雅區"]

    for i in range(1, 6):
        uid = str(uuid.uuid4())
        birthdate = date(2003 + i, i, i)
        password = generate_password()
        m = Member(
            member_id=uid,
            email=f"user{i}@example.com",
            password=password,
            name=f"User{i}",
            gender="M" if i % 2 == 0 else "F",
            birthdate=birthdate,
            height=160 + i,
            weight=50 + i * 2,
            created_at=now,
            updated_at=now,
            city=cities[i - 1],
            area=areas[i - 1],
        )
        members.append(m)

    session.add_all(members)
    session.flush()

    # 運動名稱列表
    names = ["跑步", "羽球", "瑜珈", "健身", "騎腳踏車", "籃球", "游泳", "排球", "網球", "桌球", "拳擊", "足球"]
    # 運動類型資料創建
    sport_types = [
    SportType(name=names[i])
    for i in range(12)
    ]
    session.add_all(sport_types)
    session.flush()

    activities = []
    for i in range(1, 6):
        a = Activity(
            activity_id=i,
            title=f"Activity{i}",
            time=now,
            location_name=f"Location{i}",
            location_lat=25.0 + i * 0.01,
            location_lng=121.5 + i * 0.01,
            max_participants=10 + i,
            organizer_id=members[i - 1].member_id,
            level="easy" if i % 2 == 0 else "medium",
            sport_type_id=sport_types[i - 1].sport_type_id,
            description=f"Description for Activity{i}",
            status="open",
            created_at=now,
            has_review=False,
        )
        activities.append(a)
    session.add_all(activities)
    session.flush()

    records = []
    for i in range(1, 6):
        rec = ExerciseRecord(
            record_id=i,
            member_id=members[i % 5].member_id,
            sport_type_id=sport_types[i % 5].sport_type_id,
            location=f"Gym{i}",
            location_lat=25.1 + i * 0.01,
            location_lng=121.6 + i * 0.01,
            duration_hours=1.0 + i * 0.1,
            record_date=now.date(),
            intensity_level="high" if i % 2 else "low",
            notes=f"Notes {i}",
        )
        records.append(rec)
    session.add_all(records)

    prefs = []
    for i in range(1, 6):
        match_gender = "不限"  # 這裡可以是來自前端的資料，或者是硬編碼的預設值
        match_age = "18-25"   # 同上，可以根據需求改為不同的年齡區間
        pref = SportPreference(
            preference_id=i,
            member_id=members[i - 1].member_id,
            match_gender=match_gender,  # 填入性別
            match_age=match_age         # 填入年齡區間
            
        )
        prefs.append(pref)
    session.add_all(prefs)

    reviews = []
    for i in range(1, 6):
        rev = UserReview(
            review_id=i,
            reviewer_id=members[i % 5].member_id,
            target_member_id=members[i - 1].member_id,
            rating=(i % 5) + 1,
            comment=f"Review {i}",
            created_time=now,
        )
        reviews.append(rev)
    session.add_all(reviews)

    joins = []
    for i in range(1, 6):
        j = ActivityJoin(
            join_id=i,
            member_id=members[(i + 1) % 5].member_id,
            activity_id=activities[i - 1].activity_id,
            join_time=now,
            status="joined" if i % 2 else "pending",
        )
        joins.append(j)
    session.add_all(joins)

    act_revs = []
    for i in range(1, 6):
        ar = ActivityReview(
            review_id=i,
            activity_id=activities[i - 1].activity_id,
            reviewer_id=members[(i + 2) % 5].member_id,
            rating=(i % 5) + 1,
            comment=f"ActivityReview {i}",
            created_time=now,
        )
        act_revs.append(ar)
    session.add_all(act_revs)

    time_options = [
        TimeOption(period="平日", time_of_day="早上", label="平日早上"),
        TimeOption(period="平日", time_of_day="中午", label="平日中午"),
        TimeOption(period="平日", time_of_day="晚上", label="平日晚上"),
        TimeOption(period="週末", time_of_day="早上", label="週末早上"),
        TimeOption(period="週末", time_of_day="中午", label="週末中午"),
        TimeOption(period="週末", time_of_day="晚上", label="週末晚上"),
    ]
    session.add_all(time_options)

    session.commit()


def downgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    session.query(ActivityReview).filter(ActivityReview.review_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(ActivityJoin).filter(ActivityJoin.join_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(UserReview).filter(UserReview.review_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(SportPreference).filter(SportPreference.preference_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(ExerciseRecord).filter(ExerciseRecord.record_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(Activity).filter(Activity.activity_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(SportType).filter(SportType.sport_type_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(TimeOption).filter(TimeOption.time_id.in_([1, 2, 3, 4, 5, 6])).delete()
    session.query(Member).filter(Member.email.in_([
        "user1@example.com",
        "user2@example.com",
        "user3@example.com",
        "user4@example.com",
        "user5@example.com",
    ])).delete()

    session.commit()