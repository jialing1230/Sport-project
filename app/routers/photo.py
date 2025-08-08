
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from app.database import get_db
from app.models.photo import Photo
from app.models.member import Member


photo_bp = Blueprint('photo', __name__)

@photo_bp.route('/api/upload_photo', methods=['POST'])
def upload_photo():
    member_id = request.form.get('member_id')
    file = request.files.get('file')
    if not member_id or not file:
        return jsonify({'error': '缺少 member_id 或檔案'}), 400

    with get_db() as db:
        # 查詢會員是否存在
        member = db.query(Member).filter_by(member_id=member_id).first()
        if not member:
            return jsonify({'error': '會員不存在'}), 404

        # 查詢已上傳照片數
        photo_count = db.query(Photo).filter_by(member_id=member_id).count()
        if photo_count >= 5:
            return jsonify({'error': '最多只能上傳 5 張照片，請先刪除舊照片'}), 400

        # 僅允許圖片副檔名
        allowed_ext = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_ext:
            return jsonify({'error': '僅允許上傳圖片檔案'}), 400

        # 儲存檔案（會員專屬資料夾，檔名加時間戳）
        import time
        timestamp = int(time.time())
        member_folder = os.path.join(current_app.root_path, 'static', 'avatars', member_id)
        os.makedirs(member_folder, exist_ok=True)
        new_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(member_folder, new_filename)
        file.save(file_path)

        # 寫入資料庫，存相對路徑
        db_path = f'static/avatars/{member_id}/{new_filename}'
        photo = Photo(file_path=db_path, member_id=member_id)
        db.add(photo)
        db.commit()

        return jsonify({'message': '上傳成功', 'file_path': photo.file_path})
