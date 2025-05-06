"""insert_5_default_records

Revision ID: f47ac10b58cc
Revises: 9dde57c6fd53
Create Date: 2025-04-19 20:30:00.000000
"""

import uuid
import random
import string
from datetime import datetime, date, timedelta
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
    PreferenceSport,
    PreferenceTime,
)

revision: str = "f47ac10b58cc"
down_revision: Union[str, None] = "9dde57c6fd53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    while True:
        pw = "".join(random.choices(chars, k=length))
        if (
            any(c.islower() for c in pw)
            and any(c.isupper() for c in pw)
            and any(c.isdigit() for c in pw)
        ):
            return pw


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    now = datetime.now()

    members = []
    cities = ["台北市", "新北市", "桃園市", "台中市", "高雄市"]
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
            gender="男" if i % 2 == 0 else "女",
            birthdate=birthdate,
            height=160 + i,
            weight=50 + i * 2,
            created_at=now,
            updated_at=now,
            city=cities[i - 1],
            area=areas[i - 1],
            is_first_login=False,
            is_unfinish_preference=False,
        )
        members.append(m)

    session.add_all(members)
    session.flush()

    names = [
        "跑步",
        "羽球",
        "瑜珈",
        "健身",
        "騎腳踏車",
        "籃球",
        "游泳",
        "排球",
        "網球",
        "桌球",
        "拳擊",
        "足球",
    ]
    sport_types = [SportType(name=names[i]) for i in range(12)]
    session.add_all(sport_types)
    session.flush()

    location_data = [
    ("臺北市松山運動中心", 25.04882705227739, 121.55032032150095),
    ("新北市板橋國民運動中心", 25.02287397065614, 121.45770633684279),
    ("桃園市桃園國民運動中心", 24.998268624636584, 121.3209204098562),
    ("臺中市北區國民運動中心", 24.15730277802729, 120.68406857913797),
    ("高雄市鳳山運動園區", 22.62152875490125, 120.3535411637387)
    ]
    activities = []
    for i in range(1, 6):
        name, lat, lng = location_data[i - 1]

        activity_start = now if i <= 2 else now + timedelta(days=2)
        activity_end = activity_start + timedelta(hours=1)
        a = Activity(
            activity_id=i,
            title=f"Activity{i}",
            start_time=activity_start,
            end_time=activity_end, 
            location_name=name,
            location_lat=lat,
            location_lng=lng,
            max_participants=2 + i,
            current_participants=2,
            organizer_id=members[i - 1].member_id,
            level="初學" if i % 2 == 0 else "中階",
            sport_type_id=sport_types[i - 1].sport_type_id,
            description=f"Description for Activity{i}",
            status="open",
            created_at=now,
            has_review=False,
            target_identity="不限",
            gender="不限",
            age_range="18-25",
            venue_fee=800.00,  
            registration_deadline=activity_start - timedelta(days=1), 
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
        pref = SportPreference(
            preference_id=i,
            member_id=members[i - 1].member_id,
            match_gender="不限",
            match_age="18-25",
        )
        prefs.append(pref)
    session.add_all(prefs)
    session.flush()

    pref_sports = []
    for pref in prefs:
        for st in sport_types:
            pref_sports.append(
                PreferenceSport(
                    preference_id=pref.preference_id,
                    sport_type_id=st.sport_type_id,
                )
            )
    session.add_all(pref_sports)

    time_options = [
        TimeOption(period="平日", time_of_day="早上", label="平日早上"),
        TimeOption(period="平日", time_of_day="中午", label="平日中午"),
        TimeOption(period="平日", time_of_day="晚上", label="平日晚上"),
        TimeOption(period="週末", time_of_day="早上", label="週末早上"),
        TimeOption(period="週末", time_of_day="中午", label="週末中午"),
        TimeOption(period="週末", time_of_day="晚上", label="週末晚上"),
    ]
    session.add_all(time_options)
    session.flush()

    pref_times = []
    for pref in prefs:
        for to in time_options:
            pref_times.append(
                PreferenceTime(
                    preference_id=pref.preference_id,
                    time_id=to.time_id,
                )
            )
    session.add_all(pref_times)

    reviews = []
    for i in range(1, 6):
        reviews.append(
            UserReview(
                review_id=i,
                reviewer_id=members[i % 5].member_id,
                target_member_id=members[i - 1].member_id,
                rating=(i % 5) + 1,
                comment=f"Review {i}",
                created_time=now,
            )
        )
    session.add_all(reviews)

    joins = []
    for i in range(1, 6):
        joins.append(
            ActivityJoin(
                join_id=i,
                member_id=members[(i + 1) % 5].member_id,
                activity_id=activities[i - 1].activity_id,
                join_time=now,
                status="joined",
            )
        )

    for i in range(6, 11):
        joins.append(
            ActivityJoin(
                join_id=i,
                member_id=members[(i + 2) % 5].member_id,
                activity_id=activities[(i - 6) % 5].activity_id,
                join_time=now,
                status="pending",
            )
        )
        
    session.add_all(joins)

    act_revs = []
    for i in range(1, 6):
        act_revs.append(
            ActivityReview(
                review_id=i,
                activity_id=activities[i - 1].activity_id,
                reviewer_id=members[(i + 2) % 5].member_id,
                rating=(i % 5) + 1,
                comment=f"ActivityReview {i}",
                created_time=now,
            )
        )
    session.add_all(act_revs)

    session.commit()


def downgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    # Remove linked preferences first
    session.query(PreferenceTime).filter(
        PreferenceTime.preference_id.in_([1, 2, 3, 4, 5])
    ).delete()
    session.query(PreferenceSport).filter(
        PreferenceSport.preference_id.in_([1, 2, 3, 4, 5])
    ).delete()

    session.query(ActivityReview).filter(
        ActivityReview.review_id.in_([1, 2, 3, 4, 5])
    ).delete()
    session.query(ActivityJoin).filter(
        ActivityJoin.join_id.in_([1, 2, 3, 4, 5])
    ).delete()
    session.query(UserReview).filter(UserReview.review_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(SportPreference).filter(
        SportPreference.preference_id.in_([1, 2, 3, 4, 5])
    ).delete()
    session.query(ExerciseRecord).filter(
        ExerciseRecord.record_id.in_([1, 2, 3, 4, 5])
    ).delete()
    session.query(Activity).filter(Activity.activity_id.in_([1, 2, 3, 4, 5])).delete()
    session.query(SportType).filter(
        SportType.sport_type_id.in_([1, 2, 3, 4, 5])
    ).delete()
    session.query(TimeOption).filter(
        TimeOption.time_id.in_([1, 2, 3, 4, 5, 6])
    ).delete()
    session.query(Member).filter(
        Member.email.in_(
            [
                "user1@example.com",
                "user2@example.com",
                "user3@example.com",
                "user4@example.com",
                "user5@example.com",
            ]
        )
    ).delete()

    session.commit()
