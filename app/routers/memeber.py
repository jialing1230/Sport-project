from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.member import Member

member_bp = Blueprint("members", __name__, url_prefix="/api/members")


@member_bp.route("", methods=["POST"])
def create_member():
    """
    建立一個新 Member：
    必填欄位：email, password
    其餘欄位可選
    """
    payload = request.get_json()
    required = ("email", "password")
    for key in required:
        if key not in payload:
            return jsonify({"error": f"缺少欄位 {key}"}), 400

    with get_db() as db:
        m = Member(
            member_id=payload.get("member_id"),
            email=payload["email"],
            password=payload["password"],
            name=payload.get("name"),
            gender=payload.get("gender"),
            birthdate=payload.get("birthdate"),
            height=payload.get("height"),
            weight=payload.get("weight"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(m)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return jsonify({"error": "Email 重複"}), 400
        db.refresh(m)

    return jsonify({"member_id": m.member_id}), 201


@member_bp.route("", methods=["GET"])
def list_members():
    """
    列出所有 Member（回傳最基本的欄位）
    """
    with get_db() as db:
        members = db.query(Member).all()

    result = []
    for u in members:
        result.append(
            {
                "member_id": u.member_id,
                "email": u.email,
                "name": u.name,
                "gender": u.gender,
                "birthdate": u.birthdate.isoformat() if u.birthdate else None,
                "height": u.height,
                "weight": u.weight,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            }
        )
    return jsonify(result), 200


@member_bp.route("/<int:member_id>", methods=["GET"])
def get_member(member_id):
    """
    根據 ID 取得單一 Member
    """
    with get_db() as db:
        u = db.get(Member, member_id)
        if not u:
            return jsonify({"error": "找不到該會員"}), 404

    return jsonify(
        {
            "member_id": u.member_id,
            "email": u.email,
            "name": u.name,
            "gender": u.gender,
            "birthdate": u.birthdate.isoformat() if u.birthdate else None,
            "height": u.height,
            "weight": u.weight,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
        }
    ), 200
