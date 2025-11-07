from flask import Blueprint, request, jsonify
from datetime import datetime
from app.database import get_db
from app.models.activity_comment import ActivityComment
from app.models.activity import Activity
from app.models.member import Member
from app.models.notification import Notification


activity_comment_bp = Blueprint("activity_comment", __name__, url_prefix="/api/activity_comments")
def serialize_comment(comment):
    return {
        "comment_id": comment.comment_id,
        "activity_id": comment.activity_id,
        "member_id": comment.member_id,
        "parent_id": comment.parent_id,
        "member_name": getattr(comment, '_member_name', None),
        "content": comment.content,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
        "is_deleted": comment.is_deleted,
        "is_pinned": comment.is_pinned,
    }


@activity_comment_bp.route("/", methods=["POST"])
def create_comment():
    data = request.get_json() or {}
    activity_id = data.get("activity_id")
    member_id = data.get("member_id")
    content = data.get("content")
    parent_id = data.get("parent_id")

    if not activity_id or not member_id or not content:
        return jsonify({"error": "缺少必要欄位 (activity_id/member_id/content)"}), 400

    comment_id = None
    with get_db() as db:
        activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
        if not activity:
            return jsonify({"error": "活動不存在"}), 404
        member = db.query(Member).filter(Member.member_id == member_id).first()
        if not member:
            return jsonify({"error": "會員不存在"}), 404

        comment = ActivityComment(
            activity_id=activity_id,
            member_id=member_id,
            parent_id=parent_id,
            content=content,
            created_at=datetime.now(),
            is_deleted=False,
            is_pinned=False,
        )
        db.add(comment)
        db.commit()
        # 確保 PK 已被後端填好，先抓出 id 再離開 session
        try:
            db.refresh(comment)
        except Exception:
            # refresh 不是必要的，只要能取得 PK 即可
            pass
        comment_id = getattr(comment, 'comment_id', None)

        # 可選：通知主辦人（如果留言者不是主辦人）
        try:
            if activity.organizer_id and activity.organizer_id != member_id:
                note = Notification(
                    member_id=activity.organizer_id,
                    title="活動留言通知",
                    content=f"{member.name if member else '有人'} 在您的活動「{activity.title if activity else ''}」留言：{content[:50]}",
                    url=f"/api/activities/details_page?id={activity_id}&member_id={activity.organizer_id}",
                )
                db.add(note)
                db.commit()
        except Exception:
            # 不應阻斷主要流程
            db.rollback()
        # 若為回覆，通知被回覆的人（但不要通知自己）
        try:
            if parent_id:
                parent = db.query(ActivityComment).filter(ActivityComment.comment_id == parent_id).first()
                if parent and getattr(parent, 'member_id', None) and str(parent.member_id) != str(member_id):
                    note2 = Notification(
                        member_id=parent.member_id,
                        title="留言回覆通知",
                        content=f"{member.name if member else '有人'} 回覆了你的留言：{content[:50]}",
                        url=f"/api/activities/details_page?id={activity_id}&member_id={parent.member_id}#comment-{comment_id}",
                    )
                    db.add(note2)
                    db.commit()
        except Exception:
            # 回覆通知失敗也不應阻斷主要流程
            db.rollback()
        

    return jsonify({"comment_id": comment_id}), 201


@activity_comment_bp.route("/activity/<int:activity_id>", methods=["GET"])
def list_comments(activity_id):
    with get_db() as db:
        # only include comments that are not soft-deleted
        comments = (
            db.query(ActivityComment)
            .filter(ActivityComment.activity_id == activity_id, ActivityComment.is_deleted.is_(False))
            .order_by(ActivityComment.created_at.asc())
            .all()
        )

        # fetch member names for all involved member_ids to avoid N+1 queries
        member_ids = {c.member_id for c in comments if c.member_id is not None}
        member_map = {}
        if member_ids:
            members = db.query(Member).filter(Member.member_id.in_(member_ids)).all()
            member_map = {m.member_id: m.name for m in members}

        # attach member_name onto comment objects for serializer
        for c in comments:
            setattr(c, '_member_name', member_map.get(c.member_id))

        # build tree
        by_id = {c.comment_id: c for c in comments}
        roots = []
        for c in comments:
            if c.parent_id is None:
                roots.append(c)
            else:
                parent = by_id.get(c.parent_id)
                if parent:
                    # ensure replies list exists on object for serialization
                    if not hasattr(parent, '_replies'):
                        parent._replies = []
                    parent._replies.append(c)

        def build(c):
            item = serialize_comment(c)
            replies = getattr(c, '_replies', [])
            item['replies'] = [build(r) for r in replies]
            return item

        result = [build(r) for r in roots]
    return jsonify(result), 200


@activity_comment_bp.route("/<int:comment_id>", methods=["PUT"])
def update_comment(comment_id):
    data = request.get_json() or {}
    new_content = data.get("content")
    if not new_content:
        return jsonify({"error": "缺少 content 欄位"}), 400

    with get_db() as db:
        c = db.query(ActivityComment).filter(ActivityComment.comment_id == comment_id).first()
        if not c:
            return jsonify({"error": "留言不存在"}), 404
        c.content = new_content
        c.updated_at = datetime.now()
        db.commit()
    return jsonify({"message": "更新成功"}), 200


@activity_comment_bp.route("/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    with get_db() as db:
        c = db.query(ActivityComment).filter(ActivityComment.comment_id == comment_id).first()
        if not c:
            return jsonify({"error": "留言不存在"}), 404
        # soft delete
        c.is_deleted = True
        c.updated_at = datetime.now()
        db.commit()
    return jsonify({"message": "已刪除"}), 200


@activity_comment_bp.route("/<int:comment_id>/pin", methods=["POST"])
def pin_comment(comment_id):
    data = request.get_json() or {}
    is_pinned = bool(data.get("is_pinned", True))
    with get_db() as db:
        c = db.query(ActivityComment).filter(ActivityComment.comment_id == comment_id).first()
        if not c:
            return jsonify({"error": "留言不存在"}), 404
        c.is_pinned = is_pinned
        c.updated_at = datetime.now()
        db.commit()
    return jsonify({"message": "設定成功"}), 200
