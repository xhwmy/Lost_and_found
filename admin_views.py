# Admin views module for campus crowdfunding project
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from markupsafe import escape
from models import db, User, Admin, LostItem, FoundItem, Claim, ThreadComment, Favorite, Notification, ForumPost, ForumReply, Announcement, SecurityRule, IPBan, IPWhitelist, OperationLog
from sqlalchemy import func
from flask import jsonify  # 用于返回JSON响应
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import random
import string
from utils import log_operation

def get_real_ip(request):
    """获取真实的客户端IP地址"""
    if 'X-Forwarded-For' in request.headers:
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    if 'X-Real-IP' in request.headers:
        return request.headers['X-Real-IP']
    return request.remote_addr

def validate_password_strength(password):
    """验证密码强度"""
    if len(password) < 8:
        return False, '密码长度至少8位'
    if not any(char.isupper() for char in password):
        return False, '密码至少包含一个大写字母'
    if not any(char.islower() for char in password):
        return False, '密码至少包含一个小写字母'
    if not any(char.isdigit() for char in password):
        return False, '密码至少包含一个数字'
    return True, '密码强度符合要求'

admin_bp = Blueprint('admin', __name__, template_folder='templates')

def generate_captcha():
    """生成随机验证码"""
    # 生成6位随机验证码，排除易混淆字符（0, O, l, I, 1等）
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
    captcha = ''.join(random.choice(characters) for _ in range(6))
    # 存储验证码到session，有效期5分钟，同时存储原始和小写版本
    session['admin_captcha'] = captcha
    session['admin_captcha_lower'] = captcha.lower()
    session['admin_captcha_time'] = datetime.now().timestamp()
    print(f"[ADMIN CAPTCHA] 生成新验证码: '{captcha}'")
    return captcha

def get_admin_captcha():
    """获取当前管理员验证码，如果session中没有或已过期则生成新的"""
    stored_captcha = session.get('admin_captcha')
    stored_captcha_lower = session.get('admin_captcha_lower')
    captcha_time = session.get('admin_captcha_time', 0)
    current_time = datetime.now().timestamp()
    
    print(f"[ADMIN CAPTCHA] 检查验证码: 存储的='{stored_captcha}', 小写='{stored_captcha_lower}', 时间差={current_time - captcha_time:.2f}秒")
    
    # 如果验证码不存在、小写版本不存在或已过期（5分钟），生成新的
    if not stored_captcha or not stored_captcha_lower or (current_time - captcha_time > 300):
        print("[ADMIN CAPTCHA] 验证码不存在或已过期，生成新的")
        return generate_captcha()
    
    # 确保captcha_lower与captcha匹配
    if stored_captcha_lower != stored_captcha.lower():
        print("[ADMIN CAPTCHA] captcha_lower与captcha不匹配，重新生成")
        return generate_captcha()
    
    print(f"[ADMIN CAPTCHA] 使用现有验证码: '{stored_captcha}'")
    return stored_captcha

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        captcha = request.form.get('captcha', '').strip().lower()  # 去除首尾空格
        ip_address = get_real_ip(request)

        # 验证验证码
        stored_captcha = session.get('admin_captcha')
        stored_captcha_lower = session.get('admin_captcha_lower')
        captcha_time = session.get('admin_captcha_time', 0)
        current_time = datetime.now().timestamp()
        
        print(f"[ADMIN CAPTCHA] 登录 - 用户输入: '{captcha}'")
        print(f"[ADMIN CAPTCHA] 登录 - 存储的原始: '{stored_captcha}'")
        print(f"[ADMIN CAPTCHA] 登录 - 存储的小写: '{stored_captcha_lower}'")
        
        # 验证码验证 - 优先检查是否过期
        if not stored_captcha or not stored_captcha_lower:
            flash('验证码已过期，请刷新页面重试', 'danger')
            current_captcha = get_admin_captcha()
            return render_template('admin/login.html', captcha=current_captcha)
        
        if current_time - captcha_time > 300:  # 5分钟过期
            flash('验证码已过期，请刷新页面重试', 'danger')
            current_captcha = get_admin_captcha()
            return render_template('admin/login.html', captcha=current_captcha)
        
        if not captcha:
            flash('请输入验证码', 'danger')
            return render_template('admin/login.html', captcha=stored_captcha)
        
        if captcha != stored_captcha_lower:
            # 验证码错误时生成新的验证码
            flash('验证码错误，请重试', 'danger')
            current_captcha = generate_captcha()
            return render_template('admin/login.html', captcha=current_captcha)

        # 检查IP是否在白名单中（只有白名单IP才能登录管理员账户）
        # 如果白名单为空，则允许所有IP访问
        whitelist_count = IPWhitelist.query.filter_by(is_active=True).count()
        print(f"[WHITELIST DEBUG] 白名单IP数量: {whitelist_count}")
        print(f"[WHITELIST DEBUG] 当前IP: {ip_address}")
        
        whitelist_entry = IPWhitelist.query.filter_by(ip_address=ip_address, is_active=True).first()
        is_whitelisted = whitelist_count == 0 or whitelist_entry is not None
        print(f"[WHITELIST DEBUG] 白名单匹配: {whitelist_entry}")
        print(f"[WHITELIST DEBUG] 是否白名单: {is_whitelisted}")
        
        if not is_whitelisted:
            flash('您的IP地址不在白名单中，无法登录管理员账户', 'danger')
            log_operation('admin', 0, 'IP白名单检测', f'IP: {ip_address} 尝试登录管理员账户但不在白名单中')
            return render_template('admin/login.html', captcha=stored_captcha)
        
        # 检查IP是否被封禁（白名单IP也可能被管理员手动封禁）
        ip_ban = IPBan.query.filter_by(ip_address=ip_address).first()
        if ip_ban and ip_ban.is_banned():
            flash('您的IP地址已被封禁，请联系超级管理员', 'danger')
            log_operation('admin', 0, 'IP封禁检测', f'IP: {ip_address} 尝试登录但已被封禁')
            return render_template('admin/login.html', captcha=stored_captcha)

        # 查询管理员
        admin = Admin.query.filter_by(username=username).first()

        # 检查管理员是否存在
        if admin:
            # 检查密码是否正确
            if admin.check_password(password):
                # 登录成功，清除验证码
                session.pop('admin_captcha', None)
                session.pop('admin_captcha_lower', None)
                session.pop('admin_captcha_time', None)
                
                # 登录成功
                session['admin_id'] = admin.id
                session['admin_username'] = admin.username
                db.session.commit()

                log_operation('admin', admin.id, '管理员登录', f'管理员 {admin.username} 登录系统，IP: {ip_address}')
                flash('登录成功！', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('用户名或密码错误', 'danger')
                current_captcha = generate_captcha()
                return render_template('admin/login.html', captcha=current_captcha)
        else:
            # Log the failed attempt
            log_operation('admin', 0, '无效管理员登录尝试', f'IP: {ip_address}, Username: {username}')
            flash('用户名或密码错误', 'danger')
            current_captcha = generate_captcha()
            return render_template('admin/login.html', captcha=current_captcha)

    # GET请求时获取验证码（如果存在且未过期则使用现有验证码）
    captcha = get_admin_captcha()
    return render_template('admin/login.html', captcha=captcha)

@admin_bp.route('/admin/logout')
def logout():
    if 'admin_id' in session:
        # 使用字符串拼接避免引号问题
        username = session.get('admin_username', 'unknown')
        log_operation('admin', session['admin_id'], '管理员登出', '管理员 ' + username + ' 登出系统')
    session.clear()
    flash('您已成功登出', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/admin/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))

    # 统计数据
    total_users = User.query.count()
    total_lost_items = LostItem.query.count()
    total_found_items = FoundItem.query.count()
    total_claims = Claim.query.count()

    # 待审核数据
    pending_lost_items = LostItem.query.filter_by(status='pending').count()
    pending_found_items = FoundItem.query.filter_by(status='pending').count()
    pending_claims = Claim.query.filter_by(status='pending').count()
    
    # 计算状态分布数据
    approved_lost_items = LostItem.query.filter_by(status='approved').count()
    rejected_lost_items = LostItem.query.filter_by(status='rejected').count()
    completed_lost_items = LostItem.query.filter_by(status='completed').count()
    
    approved_found_items = FoundItem.query.filter_by(status='approved').count()
    rejected_found_items = FoundItem.query.filter_by(status='rejected').count()
    completed_found_items = FoundItem.query.filter_by(status='completed').count()
    
    # 计算安全值避免除零错误
    total_lost_safe = max(total_lost_items, 1)
    total_found_safe = max(total_found_items, 1)
    
    # 计算活跃用户统计
    from datetime import datetime, timedelta
    today_start = datetime.combine(datetime.today(), datetime.min.time())
    daily_active_users = User.query.join(LostItem, User.id == LostItem.creator_id, isouter=True).filter(
        (LostItem.created_at >= today_start) | (LostItem.updated_at >= today_start)
    ).distinct(User.id).count()
    
    monthly_new_users = User.query.filter(
        User.created_at >= datetime.now() - timedelta(days=30)
    ).count()
    
    # 系统日志统计
    system_logs_count = OperationLog.query.count()
    
    # 创建stats字典
    stats = {
        'total_users': total_users,
        'total_lost_items': total_lost_items,
        'total_found_items': total_found_items,
        'total_claims': total_claims,
        'pending_lost_items': pending_lost_items,
        'pending_found_items': pending_found_items,
        'pending_claims': pending_claims,
        'approved_lost_items': approved_lost_items,
        'rejected_lost_items': rejected_lost_items,
        'completed_lost_items': completed_lost_items,
        'approved_found_items': approved_found_items,
        'rejected_found_items': rejected_found_items,
        'completed_found_items': completed_found_items,
        'daily_active_users': daily_active_users,
        'monthly_new_users': monthly_new_users,
        'system_logs_count': system_logs_count
    }
    
    return render_template('admin/dashboard.html', 
                           stats=stats,
                           total_lost_safe=total_lost_safe,
                           total_found_safe=total_found_safe)

@admin_bp.route('/admin/users')
def users():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # 如果有搜索参数，则过滤查询
    if search:
        users = User.query.filter(User.username.contains(search)).paginate(page=page, per_page=10, error_out=False)
    else:
        users = User.query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/users.html', pagination=users, search=search)

@admin_bp.route('/admin/freeze-user/<int:user_id>', methods=['POST'])
def freeze_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    user = User.query.get_or_404(user_id)
    user.is_frozen = True
    db.session.commit()
    
    flash('用户冻结成功', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/admin/unfreeze-user/<int:user_id>', methods=['POST'])
def unfreeze_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    user = User.query.get_or_404(user_id)
    user.is_frozen = False
    db.session.commit()
    
    flash('用户解冻成功', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/admin/unfreeze-account/<int:account_id>', methods=['POST'])
def unfreeze_account(account_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    account_type = request.args.get('account_type', 'user')
    
    if account_type == 'admin':
        account = Admin.query.get_or_404(account_id)
    else:
        account = User.query.get_or_404(account_id)
    
    account.is_frozen = False
    db.session.commit()
    
    flash('账户解冻成功', 'success')
    return redirect(url_for('admin.frozen_accounts', type=account_type))

@admin_bp.route('/admin/lost-items')
def lost_items():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')  # 获取状态参数
    
    # 根据状态筛选查询
    if status:
        lost_items = LostItem.query.filter_by(status=status).paginate(page=page, per_page=10, error_out=False)
    else:
        lost_items = LostItem.query.paginate(page=page, per_page=10, error_out=False)
    
    # 计算待审核数量
    pending_count = LostItem.query.filter_by(status='pending').count()
    
    return render_template('admin/lost_items.html', pagination=lost_items, status=status, pending_count=pending_count)

@admin_bp.route('/admin/approve-lost-item/<int:item_id>', methods=['POST'])
def approve_lost_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    item = LostItem.query.get_or_404(item_id)
    
    # 更新失物物品状态
    item.status = 'approved'
    
    db.session.commit()
    
    flash('失物信息已通过审核', 'success')
    log_operation('admin', session['admin_id'], '审核失物', f'通过了失物信息审核: {item.id}')
    
    return redirect(url_for('admin.lost_items'))


@admin_bp.route('/admin/reject-lost-item/<int:item_id>', methods=['POST'])
def reject_lost_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    item = LostItem.query.get_or_404(item_id)
    
    # 更新失物物品状态为驳回
    item.status = 'rejected'
    item.reject_reason = request.form.get('reason', '')
    
    db.session.commit()
    
    flash('失物信息已驳回', 'warning')
    log_operation('admin', session['admin_id'], '审核失物', f'驳回了失物信息: {item.id}')
    
    return redirect(url_for('admin.lost_items'))


@admin_bp.route('/admin/found-items')
def found_items():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')  # 获取状态参数
    
    # 根据状态筛选查询
    if status:
        found_items = FoundItem.query.filter_by(status=status).paginate(page=page, per_page=10, error_out=False)
    else:
        found_items = FoundItem.query.paginate(page=page, per_page=10, error_out=False)
    
    # 计算待审核数量
    pending_count = FoundItem.query.filter_by(status='pending').count()
    
    return render_template('admin/found_items.html', pagination=found_items, status=status, pending_count=pending_count)

@admin_bp.route('/admin/approve-found-item/<int:item_id>', methods=['POST'])
def approve_found_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    item = FoundItem.query.get_or_404(item_id)
    
    # 更新招领物品状态
    item.status = 'approved'
    
    db.session.commit()
    
    flash('招领信息已通过审核', 'success')
    log_operation('admin', session['admin_id'], '审核招领', f'通过了招领信息审核: {item.id}')
    
    return redirect(url_for('admin.found_items'))


@admin_bp.route('/admin/reject-found-item/<int:item_id>', methods=['POST'])
def reject_found_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    item = FoundItem.query.get_or_404(item_id)
    
    # 更新招领物品状态为驳回
    item.status = 'rejected'
    item.reject_reason = request.form.get('reason', '')
    
    db.session.commit()
    
    flash('招领信息已驳回', 'warning')
    log_operation('admin', session['admin_id'], '审核招领', f'驳回了招领信息: {item.id}')
    
    return redirect(url_for('admin.found_items'))


@admin_bp.route('/admin/claims')
def claims():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')  # 获取状态参数
    
    # 根据状态筛选查询
    if status:
        claims = Claim.query.filter_by(status=status).paginate(page=page, per_page=10, error_out=False)
    else:
        claims = Claim.query.paginate(page=page, per_page=10, error_out=False)
    
    # 计算待审核数量
    pending_count = Claim.query.filter_by(status='pending').count()
    
    return render_template('admin/claims.html', pagination=claims, status=status, pending_count=pending_count)

@admin_bp.route('/admin/approve-claim/<int:claim_id>', methods=['POST'])
def approve_claim(claim_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    claim = Claim.query.get_or_404(claim_id)
    
    # 更新认领状态
    claim.status = 'approved'
    claim.reviewed_at = datetime.now()
    claim.reviewed_by = session['admin_id']
    claim.note = request.form.get('note', '')
    
    # 如果认领关联到失物，则更新失物状态为已完成
    if claim.lost_item:
        claim.lost_item.status = 'completed'
    
    # 如果认领关联到招领，则更新招领状态为已完成
    if claim.found_item:
        claim.found_item.status = 'completed'
    
    db.session.commit()
    
    flash('认领申请已通过', 'success')
    log_operation('admin', session['admin_id'], '审核认领', f'通过了认领申请: {claim.id}')
    
    return redirect(url_for('admin.claims'))

@admin_bp.route('/admin/reject-claim/<int:claim_id>', methods=['POST'])
def reject_claim(claim_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    claim = Claim.query.get_or_404(claim_id)
    
    # 更新认领状态为驳回
    claim.status = 'rejected'
    claim.reviewed_at = datetime.now()
    claim.reviewed_by = session['admin_id']
    claim.note = request.form.get('note', '')
    
    db.session.commit()
    
    flash('认领申请已驳回', 'warning')
    log_operation('admin', session['admin_id'], '审核认领', f'驳回了认领申请: {claim.id}')
    
    return redirect(url_for('admin.claims'))

@admin_bp.route('/admin/forum')
def forum():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    
    # 查询所有帖子（不分页）
    all_posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    
    # 为每个帖子实时计算回复数（和详情页面一样的逻辑）
    processed_posts = []
    for post in all_posts:
        # 实时查询该帖子的回复数（和详情页面完全一样的查询逻辑）
        reply_count = ForumReply.query.filter_by(post_id=post.id).count()
        
        # 处理作者名称
        if post.is_admin_post:
            author_name = '管理员'
        elif post.user_id:
            user = User.query.get(post.user_id)
            author_name = user.username if user else f'用户{post.user_id}'
        else:
            author_name = '匿名用户'
        
        # 创建包含实时回复数和作者名称的元组
        processed_post = (post, reply_count, author_name)
        processed_posts.append(processed_post)
    
    # 手动分页
    total = len(processed_posts)
    start_index = (page - 1) * 10
    end_index = start_index + 10
    paginated_posts = processed_posts[start_index:end_index]
    
    # 构建分页对象
    class CustomPagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
        
        def iter_pages(self):
            start = max(1, self.page - 2)
            end = min(self.pages + 1, self.page + 3)
            return range(start, end)
    
    posts = CustomPagination(paginated_posts, page, 10, total)
        
    return render_template('admin/forum.html', pagination=posts)

@admin_bp.route('/admin/forum-post/<int:post_id>')
def forum_post_detail(post_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    # 确保post_id是int类型
    try:
        post_id = int(post_id)
    except (TypeError, ValueError):
        flash('无效的帖子ID', 'danger')
        return redirect(url_for('admin.forum'))
    
    # 查询帖子，管理员可以看到所有帖子（包括已删除的）
    post = ForumPost.query.filter_by(id=post_id).first_or_404()
    
    # 获取分页的回复
    page = request.args.get('page', 1, type=int)
    
    # 先查询原始数据，看数据库里到底有没有对应回复（管理员可以看到所有回复，包括已删除的）
    reply_query = ForumReply.query.filter_by(
        post_id=post_id
    ).order_by(ForumReply.created_at.desc())
    
    pagination = reply_query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/forum_post_detail.html', post=post, pagination=pagination)

@admin_bp.route('/admin/reply-forum-post/<int:post_id>', methods=['POST'])
def reply_forum_post(post_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    post = ForumPost.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content:
        flash('请输入回复内容', 'danger')
        return redirect(url_for('admin.forum_post_detail', post_id=post_id))
    
    # 转义用户输入，防止XSS攻击
    content = str(escape(content))
    
    # 管理员直接发布，无需AI审核
    reply = ForumReply(
        post_id=post_id,
        user_id=None,  # 管理员回复，不设置用户ID
        content=content,
        is_deleted=False,  # 显式设置未删除状态
        admin_reply=True  # 标记为管理员回复
    )
    
    db.session.add(reply)
    # 更新帖子的回复计数
    post.reply_count = post.reply_count + 1
    db.session.commit()
    
    flash('回复发布成功', 'success')
    log_operation('admin', session['admin_id'], '回复帖子', f'回复了帖子: {post_id}')
    
    return redirect(url_for('admin.forum_post_detail', post_id=post_id))


@admin_bp.route('/admin/pin-post/<int:post_id>', methods=['POST'])
def pin_post(post_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    post = ForumPost.query.get_or_404(post_id)
    post.is_pinned = True
    post.pinned_at = datetime.now()
    db.session.commit()
    
    flash('帖子置顶成功', 'success')
    log_operation('admin', session['admin_id'], '置顶帖子', f'置顶了帖子: {post.title}')
    
    return redirect(url_for('admin.forum'))

@admin_bp.route('/admin/unpin-post/<int:post_id>', methods=['POST'])
def unpin_post(post_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    post = ForumPost.query.get_or_404(post_id)
    post.is_pinned = False
    post.pinned_at = None
    db.session.commit()
    
    flash('帖子取消置顶成功', 'success')
    log_operation('admin', session['admin_id'], '取消置顶帖子', f'取消置顶了帖子: {post.title}')
    
    return redirect(url_for('admin.forum'))

@admin_bp.route('/admin/delete-post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    post = ForumPost.query.get_or_404(post_id)
    post.is_deleted = True  # 软删除
    db.session.commit()
    
    flash('帖子删除成功', 'success')
    log_operation('admin', session['admin_id'], '删除帖子', f'删除了帖子: {post.title}')
    
    return redirect(url_for('admin.forum'))

@admin_bp.route('/admin/restore-post/<int:post_id>', methods=['POST'])
def restore_post(post_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    post = ForumPost.query.get_or_404(post_id)
    post.is_deleted = False  # 恢复帖子
    db.session.commit()
    
    flash('帖子恢复成功', 'success')
    log_operation('admin', session['admin_id'], '恢复帖子', f'恢复了帖子: {post.title}')
    
    return redirect(url_for('admin.forum'))

@admin_bp.route('/admin/create-forum-post', methods=['GET', 'POST'])
def create_forum_post():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        
        post = ForumPost(
            title=title,
            content=content,
            category=category,
            user_id=-1,  # 管理员发布的帖子，使用特殊ID表示
            is_admin_post=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('帖子发布成功', 'success')
        log_operation('admin', session['admin_id'], '发布帖子', f'发布了帖子: {title}')
        
        return redirect(url_for('admin.forum'))
    
    return render_template('admin/forum_post_form.html')

@admin_bp.route('/admin/edit-forum-post/<int:post_id>', methods=['GET', 'POST'])
def edit_forum_post(post_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    post = ForumPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.category = request.form.get('category')
        post.updated_at = datetime.now()
        
        db.session.commit()
        
        flash('帖子编辑成功', 'success')
        log_operation('admin', session['admin_id'], '编辑帖子', f'编辑了帖子: {post.title}')
        
        return redirect(url_for('admin.forum'))
    
    return render_template('admin/forum_post_form.html', post=post)

@admin_bp.route('/admin/toggle-post-status/<int:post_id>', methods=['POST'])
def toggle_post_status(post_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    post = ForumPost.query.get_or_404(post_id)
    post.is_approved = not post.is_approved  # 切换审核状态
    post.updated_at = datetime.now()
    
    db.session.commit()
    
    status_text = '通过' if post.is_approved else '驳回'
    flash(f'帖子{status_text}审核', 'success')
    log_operation('admin', session['admin_id'], f'{status_text}帖子审核', f'{status_text}了帖子: {post.title}')
    
    return redirect(url_for('admin.forum'))

@admin_bp.route('/admin/announcements')
def announcements():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    announcements = Announcement.query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/announcements.html', pagination=announcements)

@admin_bp.route('/admin/security')
def security():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    return render_template('admin/security.html')


@admin_bp.route('/admin/change-password', methods=['GET', 'POST'])
def change_password():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    admin_id = session['admin_id']
    admin = Admin.query.get_or_404(admin_id)
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证旧密码
        if not admin.check_password(old_password):
            flash('原密码错误', 'danger')
            return render_template('admin/change_password.html')
        
        # 验证密码强度
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('admin/change_password.html')
        
        # 验证两次密码是否一致
        if new_password != confirm_password:
            flash('两次密码不一致', 'danger')
            return render_template('admin/change_password.html')
        
        # 更新密码
        admin.set_password(new_password)
        db.session.commit()
        
        flash('密码修改成功，请重新登录', 'success')
        log_operation('admin', admin_id, '修改密码', f'管理员 {admin.username} 修改了密码')
        
        # 登出并跳转到登录页面
        session.clear()
        return redirect(url_for('admin.login'))
    
    return render_template('admin/change_password.html')

@admin_bp.route('/admin/frozen-accounts')
def frozen_accounts():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    account_type = request.args.get('type', 'user')
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # 根据账户类型和搜索条件进行查询
    if account_type == 'admin':
        if search:
            all_accounts = Admin.query.filter(
                (Admin.username.contains(search)) |
                (Admin.email.contains(search)) |
                (Admin.real_name.contains(search))
            ).all()
        else:
            all_accounts = Admin.query.all()
    else:
        if search:
            all_accounts = User.query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search)) |
                (User.real_name.contains(search))
            ).all()
        else:
            all_accounts = User.query.all()
    
    # 过滤被冻结的账户
    frozen_accounts_list = [{'account': account, 'type': account_type} for account in all_accounts if account.is_frozen]
    
    # 手动分页
    total = len(frozen_accounts_list)
    start = (page - 1) * 10
    end = start + 10
    paginated_accounts = frozen_accounts_list[start:end]
    
    # 计算总页数
    pages = (total + 10 - 1) // 10
    
    # 创建分页对象
    class CustomPagination:
        def __init__(self, items, page, per_page, total, pages):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = pages
            self.has_prev = page > 1
            self.has_next = end < total
            self.prev_num = page - 1
            self.next_num = page + 1
    
    accounts = CustomPagination(paginated_accounts, page, 10, total, pages)
    
    title = "被冻结的管理员账户" if account_type == 'admin' else "被冻结的用户账户"
    
    return render_template('admin/frozen_accounts.html', accounts=accounts, type=account_type, account_type=account_type, title=title, search=search)

@admin_bp.route('/admin/thread-comments')
def thread_comments():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')  # 获取状态参数
    
    # 根据状态筛选查询
    if status:
        comments = ThreadComment.query.filter_by(status=status).paginate(page=page, per_page=10, error_out=False)
    else:
        comments = ThreadComment.query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/thread_comments.html', pagination=comments, status=status)

@admin_bp.route('/admin/ip-bans')
def ip_bans():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # 如果有搜索参数，则过滤查询
    if search:
        bans = IPBan.query.filter(IPBan.ip_address.contains(search)).paginate(page=page, per_page=10, error_out=False)
    else:
        bans = IPBan.query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/ip_bans.html', pagination=bans, search=search)

@admin_bp.route('/admin/ip-whitelist')
def ip_whitelist():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    whitelists = IPWhitelist.query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/ip_whitelist.html', pagination=whitelists)

@admin_bp.route('/admin/add-ip-whitelist', methods=['POST'])
def add_ip_whitelist():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    ip_address = request.form.get('ip_address')
    description = request.form.get('description', '')
    
    # 验证IP地址格式
    import ipaddress
    try:
        ipaddress.IPv4Address(ip_address)
    except ValueError:
        try:
            ipaddress.IPv6Address(ip_address)
        except ValueError:
            flash('IP地址格式不正确', 'error')
            return redirect(url_for('admin.ip_whitelist'))
    
    # 检查是否已存在
    existing = IPWhitelist.query.filter_by(ip_address=ip_address).first()
    if existing:
        flash('该IP地址已在白名单中', 'error')
        return redirect(url_for('admin.ip_whitelist'))
    
    whitelist = IPWhitelist(
        ip_address=ip_address,
        description=description,
        is_active=True
    )
    db.session.add(whitelist)
    db.session.commit()
    
    flash('IP白名单添加成功', 'success')
    return redirect(url_for('admin.ip_whitelist'))

@admin_bp.route('/admin/delete-ip-whitelist/<int:whitelist_id>', methods=['POST'])
def delete_ip_whitelist(whitelist_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    whitelist = IPWhitelist.query.get_or_404(whitelist_id)
    db.session.delete(whitelist)
    db.session.commit()
    
    flash('IP白名单删除成功', 'success')
    return redirect(url_for('admin.ip_whitelist'))

@admin_bp.route('/admin/risk-rules', methods=['GET', 'POST'])
def risk_rules():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        # 添加新规则
        name = request.form.get('name')
        rule_type = request.form.get('rule_type')
        rule_config = request.form.get('rule_config')
        
        if name and rule_type and rule_config:
            try:
                # 验证JSON格式
                import json
                json.loads(rule_config)
                
                rule = SecurityRule(
                    name=name,
                    rule_type=rule_type,
                    rule_config=rule_config,
                    is_active=True
                )
                db.session.add(rule)
                db.session.commit()
                flash('风险规则添加成功', 'success')
            except Exception as e:
                flash(f'添加规则失败: {str(e)}', 'danger')
    
    page = request.args.get('page', 1, type=int)
    rules = SecurityRule.query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/risk_rules.html', pagination=rules)

@admin_bp.route('/admin/toggle-risk-rule/<int:rule_id>', methods=['POST'])
def toggle_risk_rule(rule_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    rule = SecurityRule.query.get_or_404(rule_id)
    rule.is_active = not rule.is_active
    db.session.commit()
    flash(f'规则已{"启用" if rule.is_active else "禁用"}', 'success')
    return redirect(url_for('admin.risk_rules'))

@admin_bp.route('/admin/delete-risk-rule/<int:rule_id>', methods=['POST'])
def delete_risk_rule(rule_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    rule = SecurityRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    flash('规则删除成功', 'success')
    return redirect(url_for('admin.risk_rules'))

@admin_bp.route('/admin/operation-logs')
def operation_logs():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    page = request.args.get('page', 1, type=int)
    operator_type = request.args.get('operator_type', '')  # 获取操作者类型参数
    
    # 根据操作者类型筛选查询
    if operator_type:
        logs = OperationLog.query.filter_by(operator_type=operator_type).paginate(page=page, per_page=10, error_out=False)
    else:
        logs = OperationLog.query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/operation_logs.html', pagination=logs, operator_type=operator_type)

@admin_bp.route('/admin/lost-items/<int:item_id>')
def lost_item_detail(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    item = LostItem.query.get_or_404(item_id)
    return render_template('admin/lost_item_detail.html', item=item)

@admin_bp.route('/admin/found-items/<int:item_id>')
def found_item_detail(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    item = FoundItem.query.get_or_404(item_id)
    return render_template('admin/found_item_detail.html', item=item)

@admin_bp.route('/admin/announcements/new', methods=['GET', 'POST'])
def create_announcement():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        announcement = Announcement(title=title, content=content)
        db.session.add(announcement)
        db.session.commit()
        
        flash('公告发布成功！', 'success')
        log_operation('admin', session['admin_id'], '发布公告', f'发布了公告: {title}')
        return redirect(url_for('admin.announcements'))
    
    return render_template('admin/announcement_form.html')

@admin_bp.route('/admin/announcements/<int:id>/edit', methods=['GET', 'POST'])
def edit_announcement(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    announcement = Announcement.query.get_or_404(id)
    
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.updated_at = datetime.now()
        
        db.session.commit()
        
        flash('公告更新成功！', 'success')
        log_operation('admin', session['admin_id'], '编辑公告', f'编辑了公告: {announcement.title}')
        return redirect(url_for('admin.announcements'))
    
    return render_template('admin/announcement_form.html', announcement=announcement)

@admin_bp.route('/admin/announcements/<int:id>/delete', methods=['POST'])
def delete_announcement(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    
    flash('公告删除成功！', 'success')
    log_operation('admin', session['admin_id'], '删除公告', f'删除了公告: {announcement.title}')
    return redirect(url_for('admin.announcements'))

@admin_bp.route('/admin/register', methods=['GET', 'POST'])
def register():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        real_name = request.form.get('real_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        captcha = request.form.get('captcha', '').strip().lower()  # 去除首尾空格
        
        # 验证验证码
        stored_captcha = session.get('admin_captcha')
        stored_captcha_lower = session.get('admin_captcha_lower')
        captcha_time = session.get('admin_captcha_time', 0)
        current_time = datetime.now().timestamp()
        
        print(f"[ADMIN CAPTCHA] 注册 - 用户输入: '{captcha}'")
        print(f"[ADMIN CAPTCHA] 注册 - 存储的原始: '{stored_captcha}'")
        print(f"[ADMIN CAPTCHA] 注册 - 存储的小写: '{stored_captcha_lower}'")
        
        # 验证码验证 - 优先检查是否过期
        if not stored_captcha or not stored_captcha_lower:
            flash('验证码已过期，请刷新页面重试', 'danger')
            current_captcha = get_admin_captcha()
            return render_template('admin/register.html', captcha=current_captcha)
        
        if current_time - captcha_time > 300:  # 5分钟过期
            flash('验证码已过期，请刷新页面重试', 'danger')
            current_captcha = get_admin_captcha()
            return render_template('admin/register.html', captcha=current_captcha)
        
        if not captcha:
            flash('请输入验证码', 'danger')
            return render_template('admin/register.html', captcha=stored_captcha)
        
        if captcha != stored_captcha_lower:
            # 关键修复：验证失败时保持原有验证码不变！
            flash('验证码错误，请重试', 'danger')
            return render_template('admin/register.html', captcha=stored_captcha)
        
        # 验证密码强度
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('admin/register.html', captcha=stored_captcha)
        
        # 验证输入
        if not username or not email or not password:
            flash('请填写所有必填字段', 'danger')
            return render_template('admin/register.html', captcha=stored_captcha)
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return render_template('admin/register.html', captcha=stored_captcha)
        
        # 检查用户名是否已存在
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            flash('用户名已存在', 'danger')
            return render_template('admin/register.html', captcha=stored_captcha)
        
        # 创建新管理员
        new_admin = Admin(
            username=username,
            email=email,
            real_name=real_name,
            role='admin'  # 默认为普通管理员
        )
        new_admin.set_password(password)
        
        try:
            db.session.add(new_admin)
            db.session.commit()
            
            # 注册成功，清除验证码
            session.pop('admin_captcha', None)
            session.pop('admin_captcha_lower', None)
            session.pop('admin_captcha_time', None)
            
            flash('管理员账号创建成功！', 'success')
            log_operation('admin', session['admin_id'], '创建管理员', f'创建了新管理员: {username}')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash('创建管理员失败，请重试', 'danger')
            return render_template('admin/register.html', captcha=stored_captcha)
    
    # GET请求时获取验证码（如果存在且未过期则使用现有验证码）
    captcha = get_admin_captcha()
    return render_template('admin/register.html', captcha=captcha)

@admin_bp.route('/admin/ban-ip', methods=['POST'])
def ban_ip():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    ip_address = request.form.get('ip_address')
    reason = request.form.get('reason', '管理员手动封禁')
    duration = request.form.get('duration', 'permanent')
    
    # 验证IP地址格式
    import ipaddress
    try:
        ipaddress.IPv4Address(ip_address)
    except ValueError:
        try:
            ipaddress.IPv6Address(ip_address)
        except ValueError:
            flash('IP地址格式不正确', 'error')
            return redirect(url_for('admin.ip_bans'))
    
    # 检查是否已存在封禁
    existing_ban = IPBan.query.filter_by(ip_address=ip_address).first()
    if existing_ban:
        # 更新现有的封禁记录
        existing_ban.reason = reason
        if duration == 'permanent':
            existing_ban.banned_until = None
        else:
            from datetime import datetime, timedelta
            if duration == '10_minutes':
                existing_ban.banned_until = datetime.now() + timedelta(minutes=10)
            elif duration == '30_minutes':
                existing_ban.banned_until = datetime.now() + timedelta(minutes=30)
            elif duration == '1_hours':
                existing_ban.banned_until = datetime.now() + timedelta(hours=1)
            elif duration == '6_hours':
                existing_ban.banned_until = datetime.now() + timedelta(hours=6)
            elif duration == '1_days':
                existing_ban.banned_until = datetime.now() + timedelta(days=1)
            elif duration == '7_days':
                existing_ban.banned_until = datetime.now() + timedelta(days=7)
        
        existing_ban.created_at = datetime.now()
    else:
        # 创建新的封禁记录
        from datetime import datetime, timedelta
        banned_until = None
        if duration != 'permanent':
            if duration == '10_minutes':
                banned_until = datetime.now() + timedelta(minutes=10)
            elif duration == '30_minutes':
                banned_until = datetime.now() + timedelta(minutes=30)
            elif duration == '1_hours':
                banned_until = datetime.now() + timedelta(hours=1)
            elif duration == '6_hours':
                banned_until = datetime.now() + timedelta(hours=6)
            elif duration == '1_days':
                banned_until = datetime.now() + timedelta(days=1)
            elif duration == '7_days':
                banned_until = datetime.now() + timedelta(days=7)
        
        ban = IPBan(
            ip_address=ip_address,
            reason=reason,
            expires_at=banned_until
        )
        db.session.add(ban)
    
    try:
        db.session.commit()
        flash('IP封禁成功', 'success')
        log_operation('admin', session['admin_id'], 'IP封禁', f'封禁了IP: {ip_address}, 原因: {reason}')
    except Exception as e:
        db.session.rollback()
        flash('IP封禁失败', 'danger')
    
    return redirect(url_for('admin.ip_bans'))


@admin_bp.route('/admin/unban-ip/<int:ban_id>', methods=['POST'])
def unban_ip(ban_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    ban = IPBan.query.get_or_404(ban_id)
    
    try:
        db.session.delete(ban)
        db.session.commit()
        flash('IP解封成功', 'success')
        log_operation('admin', session['admin_id'], 'IP解封', f'解封了IP: {ban.ip_address}')
    except Exception as e:
        db.session.rollback()
        flash('IP解封失败', 'danger')
    
    return redirect(url_for('admin.ip_bans'))


@admin_bp.route('/admin/delete-thread-comment/<int:comment_id>', methods=['POST'])
def delete_thread_comment(comment_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    comment = ThreadComment.query.get_or_404(comment_id)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('评论删除成功', 'success')
        log_operation('admin', session['admin_id'], '删除评论', f'删除了评论: {comment.id}')
    except Exception as e:
        db.session.rollback()
        flash('删除评论失败', 'danger')
    
    return redirect(url_for('admin.thread_comments'))


@admin_bp.route('/admin/delete-forum-reply/<int:reply_id>', methods=['POST'])
def delete_forum_reply(reply_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    reply = ForumReply.query.get_or_404(reply_id)
    post_id = reply.post_id
    
    try:
        # 更新帖子的回复计数
        post = ForumPost.query.get(post_id)
        if post and post.reply_count > 0:
            post.reply_count = post.reply_count - 1
        
        # 软删除评论
        reply.is_deleted = True
        db.session.commit()
        
        flash('论坛评论删除成功', 'success')
        log_operation('admin', session['admin_id'], '删除论坛评论', f'删除了论坛评论: {reply.id}')
    except Exception as e:
        db.session.rollback()
        flash('删除论坛评论失败', 'danger')
    
    return redirect(url_for('admin.forum_posts'))
