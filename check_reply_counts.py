from app import create_app
from models import db, ForumPost, ForumReply

app = create_app()
with app.app_context():
    # 检查每个帖子的实际回复数
    posts = ForumPost.query.order_by(ForumPost.id).all()
    for post in posts:
        actual_reply_count = ForumReply.query.filter_by(post_id=post.id).count()
        print(f'帖子 {post.id} ({post.title[:30]}): 数据库reply_count={post.reply_count}, 实际回复数={actual_reply_count}')