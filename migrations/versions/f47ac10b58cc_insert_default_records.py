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
import json

from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.models import (
    Member,
    SportType,
    Activity,
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

    # 插入公開介紹欄位的內容
    for i, m in enumerate(members, start=1):
        m.public_intro = f"這是 User{i} 的公開介紹，歡迎大家交流！"

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
            type="activity",
            start_time=activity_start,
            end_time=activity_end, 
            location_name=name,
            location_lat=lat,
            location_lng=lng,
            max_participants=3 + i,
            current_participants=3,
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

    # 插入4筆活動時間為過去的資料
    k = 1
    past_activities = []
    for idx, i in enumerate(range(6, 10)):
        name, lat, lng = location_data[(i - 6) % len(location_data)]

        activity_start = now - timedelta(days=i)
        activity_end = activity_start + timedelta(hours=1)
        a = Activity(
            activity_id=i,
            title=f"Past Activity{i}",
            type="activity",
            start_time=activity_start,
            end_time=activity_end,
            location_name=name,
            location_lat=lat,
            location_lng=lng,
            max_participants=5 + i,
            current_participants=3,
            organizer_id=members[k - 1].member_id,
            level="中階" if i % 2 == 0 else "高階",
            sport_type_id=sport_types[(i - 6) % len(sport_types)].sport_type_id,
            description=f"Description for Past Activity{i}",
            status="closed",
            created_at=activity_start - timedelta(days=1),
            has_review=False if idx == 0 else True,
            target_identity="不限",
            gender="不限",
            age_range="20-30",
            venue_fee=500.00,
            registration_deadline=activity_start - timedelta(days=2),
        )
        past_activities.append(a)
        k += 1
    session.add_all(past_activities)
    session.flush()

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


    joins = []
    for i in range(1, 6):
        joins.append(
            ActivityJoin(
                join_id=i,
                member_id=members[(i + 1) % 5].member_id,
                activity_id=activities[i - 1].activity_id,
                join_time=now,
                status="joined",
                has_review=False,
                is_checked_in=False,
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
                has_review=False,
                is_checked_in=False,
            )
        )

    # 修正 join_id 的生成邏輯，確保從 11 到 15
    for i in range(1, 6):
        joins.append(
            ActivityJoin(
                join_id=10 + i,  # 確保 join_id 從 11 到 15
                member_id=members[(i + 3) % 5].member_id,  # 使用不同的成員
                activity_id=activities[i - 1].activity_id,
                join_time=now,
                status="joined",
                has_review=False,
                is_checked_in=False,
            )
        )
        
    session.add_all(joins)



    review_templates = [
        {
            "type": "1",
            "text": "活動開始時間混亂",
        },
        {
            "type": "1",
            "text": "主辦人臨時取消或遲到",
        },
        {
            "type": "1",
            "text": "現場混亂缺乏引導",
        },
        {
            "type": "1",
            "text": "活動與描述內容落差很大",
        },
        {
            "type": "1",
            "text": "缺乏安全與風險控管",
        },
        {
            "type": "2",
            "text": "活動內容不夠有趣",
        },
        {
            "type": "2",
            "text": "主辦人態度不友善",
        },
        {
            "type": "2",
            "text": "活動後沒有回饋或改進",
        },
        {
            "type": "2",
            "text": "缺乏活動後的社群互動",
        },
        {
            "type": "2",
            "text": "活動時間安排不合理",
        },
        {
            "type": "3",
            "text": "活動如預期進行",
        },
        {
            "type": "3",
            "text": "主辦人態度親切",
        },
        {
            "type": "3",
            "text": "地點方便但設施普通",
        },
        {
            "type": "3",
            "text": "活動氣氛普通無特別亮點",
        },
        {
            "type": "3",
            "text": "可以再參加但期望更好",
        },
        {
            "type": "4",
            "text": "活動流程安排得當",
        },
        {
            "type": "4",
            "text": "主辦人有經驗有熱情",
        },
        {
            "type": "4",
            "text": "現場氣氛熱絡",
        },
        {
            "type": "4",
            "text": "溝通順暢、資訊清楚",
        },
        {
            "type": "4",
            "text": "整體體驗良好會再參加",
        },
        {
            "type": "5",
            "text": "活動精彩超出預期",
        },
        {
            "type": "5",
            "text": "主辦人超級用心",
        },
        {
            "type": "5",
            "text": "時間掌握精準、效率高",
        },
        {
            "type": "5",
            "text": "氛圍佳、參加者配合度高",
        },
        {
            "type": "5",
            "text": "完美活動，強烈推薦！",
        },
        {
            "type": "6",
            "text": "準時性差",
        },
        {
            "type": "6",
            "text": "溝通困難",
        },
        {
            "type": "6",
            "text": "配合度不高",
        },
        {
            "type": "6",
            "text": "無故缺席",
        },
        {
            "type": "7",
            "text": "稍微遲到",
        },
        {
            "type": "7",
            "text": "態度冷淡",
        },
        {
            "type": "7",
            "text": "可再積極參與",
        },
        {
            "type": "7",
            "text": "參與度低",
        },
        {
            "type": "8",
            "text": "普通參與",
        },
         {
            "type": "8",
            "text": "表現穩定",
        },
         {
            "type": "8",
            "text": "有改進空間",
        },
        {
            "type": "8",
            "text": "過程順利",
        },
        {
            "type": "9",
            "text": "準時有禮",
        },
        {
            "type": "9",
            "text": "配合良好",
        },
        {
            "type": "9",
            "text": "氣氛不錯",
        },
        {
            "type": "9",
            "text": "態度積極",
        },
        {
            "type": "10",
            "text": "非常準時",
        },
        {
            "type": "10",
            "text": "態度極佳",
        },
        {
            "type": "10",
            "text": "積極參與",
        },
        {
            "type": "10",
            "text": "表現出色",
        },
         

    ]

    session.execute(
        text("""
        INSERT INTO review_templates (type, text)
        VALUES (:type, :text)
        """),
        review_templates,
    )

    # 修正 activity_favorite 插入邏輯，使用 UUID
    activity_favorites = [
        {
            "member_id": members[0].member_id,  # 使用第一位成員的 UUID
            "activity_id": 4,
            "created_at": now,
        },
        {
            "member_id": members[1].member_id,  # 使用第二位成員的 UUID
            "activity_id": 5,
            "created_at": now,
        },
    ]
    session.execute(
        text("""
        INSERT INTO activity_favorite (member_id, activity_id, created_at)
        VALUES (:member_id, :activity_id, :created_at)
        """),
        activity_favorites,
    )

    # 更新過去活動的參加人，確保不與發起人相同
    past_activity_joins = []
    next_join_id = max(join.join_id for join in joins) + 1  # 確保 join_id 從最大值開始遞增

    for past_activity in past_activities:
        organizer_id = past_activity.organizer_id

        # 選擇非發起人的成員作為參加人
        participant_ids = [
            member.member_id
            for member in members
            if member.member_id != organizer_id
        ]

        for idx, participant_id in enumerate(participant_ids[:2]):  # 加入兩個參加人
            # 第一個 past_activity 的兩個參加人 has_review=False，其餘為 True
            if past_activity == past_activities[0]:
                has_review_flag = False
            else:
                has_review_flag = True
            past_activity_joins.append(
                ActivityJoin(
                    join_id=next_join_id,
                    member_id=participant_id,
                    activity_id=past_activity.activity_id,
                    join_time=now - timedelta(days=1),
                    status="joined",
                    has_review=has_review_flag,
                    is_checked_in=True,
                )
            )
            next_join_id += 1

    session.add_all(past_activity_joins)
    session.flush()

    user_reviews = [
        {
            "review_id": 1,
            "reviewer_id": members[0].member_id,
            "target_member_id": members[1].member_id,
            "rating": 5,
            "created_time": now,
            "activity_id": past_activities[1].activity_id,
            "template_ids": json.dumps([43, 44]),
        },
        {
            "review_id": 2,
            "reviewer_id": members[2].member_id,
            "target_member_id": members[0].member_id,
            "rating": 3,
            "created_time": now,
            "activity_id": past_activities[2].activity_id,
            "template_ids": json.dumps([34, 35, 36]),
        },
        {
            "review_id": 3,
            "reviewer_id": members[3].member_id,
            "target_member_id": members[0].member_id,
            "rating": 2,
            "created_time": now,
            "activity_id": past_activities[3].activity_id,
            "template_ids": json.dumps([30, 31, 32]),
        },
       
    ]

    session.execute(
        text("""
        INSERT INTO user_reviews (review_id, reviewer_id, target_member_id, rating, created_time, activity_id, template_ids)
        VALUES (:review_id, :reviewer_id, :target_member_id, :rating, :created_time, :activity_id, :template_ids)
        """),
        user_reviews,
    )

    activity_reviews = [
        
        {
            "review_id": 1,
            "activity_id": past_activities[1].activity_id,
            "reviewer_id": members[0].member_id,
            "rating": 5,
            "template_ids": json.dumps([21, 22]),
            "created_time": now,
        },
        {
            "review_id": 2,
            "activity_id": past_activities[2].activity_id,
            "reviewer_id": members[0].member_id,
            "rating": 3,
            "template_ids": json.dumps([10, 11, 12]),
            "created_time": now,
        },
        {
            "review_id": 3,
            "activity_id": past_activities[3].activity_id,
            "reviewer_id": members[0].member_id,
            "rating": 2,
            "template_ids": json.dumps([6, 7, 8]),
            "created_time": now,
        },
        {
            "review_id": 4,
            "activity_id": past_activities[1].activity_id,
            "reviewer_id": members[2].member_id,
            "rating": 3,
            "template_ids": json.dumps([11, 12, 13]),
            "created_time": now,
        },
        {
            "review_id": 5,
            "activity_id": past_activities[2].activity_id,
            "reviewer_id": members[1].member_id,
            "rating": 4,
            "template_ids": json.dumps([16, 17, 18]),
            "created_time": now,
        },
        {
            "review_id": 6,
            "activity_id": past_activities[3].activity_id,
            "reviewer_id": members[1].member_id,
            "rating": 5,
            "template_ids": json.dumps([21, 22, 23]),
            "created_time": now,
        }



    ]

    session.execute(
        text("""
        INSERT INTO activity_reviews (review_id, activity_id, reviewer_id, rating, created_time, template_ids)
        VALUES (:review_id, :activity_id, :reviewer_id, :rating, :created_time, :template_ids)
        """),
        activity_reviews,
    )

    blacklist_entries = [
        {
            "member_id": members[0].member_id,
            "blocked_member_id": members[1].member_id,
            "reason": "不當行為",
            "created_at": now,
        },
        {
            "member_id": members[2].member_id,
            "blocked_member_id": members[3].member_id,
            "reason": "騷擾其他使用者",
            "created_at": now,
        },
    ]

    session.execute(
        text("""
        INSERT INTO blacklist (member_id, blocked_member_id, reason, created_at)
        VALUES (:member_id, :blocked_member_id, :reason, :created_at)
        """),
        blacklist_entries,
    )

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
