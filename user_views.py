from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from markupsafe import escape
from models import db, User, LostItem, FoundItem, Claim, ForumPost, ForumReply
from models import Notification, Favorite, Announcement, IPBan, ThreadComment, IPWhitelist
from sqlalchemy import and_, or_, text, func
from datetime import datetime, timedelta
from sqlalchemy.orm import selectinload
import time
import os
import random
import string
from utils import user_login_required, log_operation, allowed_file, moderate_and_save_content
from werkzeug.utils import secure_filename

def get_real_ip(request):
    """获取真实的客户端IP地址"""
    if 'X-Forwarded-For' in request.headers:
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    if 'X-Real-IP' in request.headers:
        return request.headers['X-Real-IP']
    return request.remote_addr

user_bp = Blueprint('user', __name__, url_prefix='/user')


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


def generate_captcha():
    """生成随机验证码"""
    # 生成6位随机验证码，排除易混淆字符（0, O, l, I, 1等）
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
    captcha = ''.join(random.choice(characters) for _ in range(6))
    # 存储验证码到session，有效期5分钟，同时存储原始和小写版本
    session['captcha'] = captcha
    session['captcha_lower'] = captcha.lower()
    session['captcha_time'] = datetime.now().timestamp()
    print(f"[CAPTCHA] 生成新验证码: '{captcha}'")
    return captcha

def get_captcha():
    """获取当前验证码，如果session中没有或已过期则生成新的"""
    stored_captcha = session.get('captcha')
    stored_captcha_lower = session.get('captcha_lower')
    captcha_time = session.get('captcha_time', 0)
    current_time = datetime.now().timestamp()
    
    print(f"[CAPTCHA] 检查验证码: 存储的='{stored_captcha}', 小写='{stored_captcha_lower}', 时间差={current_time - captcha_time:.2f}秒")
    
    # 如果验证码不存在、小写版本不存在或已过期（5分钟），生成新的
    if not stored_captcha or not stored_captcha_lower or (current_time - captcha_time > 300):
        print("[CAPTCHA] 验证码不存在或已过期，生成新的")
        return generate_captcha()
    
    # 确保captcha_lower与captcha匹配
    if stored_captcha_lower != stored_captcha.lower():
        print("[CAPTCHA] captcha_lower与captcha不匹配，重新生成")
        return generate_captcha()
    
    print(f"[CAPTCHA] 使用现有验证码: '{stored_captcha}'")
    return stored_captcha


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        captcha = request.form.get('captcha', '').strip().lower()  # 去除首尾空格
        
        # 验证验证码
        stored_captcha = session.get('captcha')
        stored_captcha_lower = session.get('captcha_lower')
        captcha_time = session.get('captcha_time', 0)
        current_time = datetime.now().timestamp()
        
        print(f"[CAPTCHA] 用户输入: '{captcha}'")
        print(f"[CAPTCHA] 存储的原始: '{stored_captcha}'")
        print(f"[CAPTCHA] 存储的小写: '{stored_captcha_lower}'")
        
        # 验证码验证 - 优先检查是否过期
        if not stored_captcha or not stored_captcha_lower:
            flash('验证码已过期，请刷新页面重试', 'danger')
            current_captcha = get_captcha()
            return render_template('user/register.html', captcha=current_captcha)
        
        if current_time - captcha_time > 300:  # 5分钟过期
            flash('验证码已过期，请刷新页面重试', 'danger')
            current_captcha = get_captcha()
            return render_template('user/register.html', captcha=current_captcha)
        
        if not captcha:
            flash('请输入验证码', 'danger')
            return render_template('user/register.html', captcha=stored_captcha)
        
        if captcha != stored_captcha_lower:
            # 关键修复：验证失败时保持原有验证码不变！
            flash('验证码错误，请重试', 'danger')
            return render_template('user/register.html', captcha=stored_captcha)
        
        # 验证密码强度
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('user/register.html', captcha=stored_captcha)
        
        # 验证
        if password != confirm_password:
            flash('两次密码不一致', 'danger')
            return render_template('user/register.html', captcha=stored_captcha)
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('user/register.html', captcha=stored_captcha)
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('user/register.html', captcha=stored_captcha)
        
        # 创建用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        log_operation('user', user.id, '用户注册')
        
        # 注册成功，清除验证码
        session.pop('captcha', None)
        session.pop('captcha_lower', None)
        session.pop('captcha_time', None)
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('user.login'))
    
    # GET请求时获取验证码（如果存在且未过期则使用现有验证码）
    captcha = get_captcha()
    return render_template('user/register.html', captcha=captcha)


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        captcha = request.form.get('captcha', '').strip().lower()  # 去除首尾空格
        ip_address = get_real_ip(request)  # 获取真实的用户IP地址
        
        # 验证验证码
        stored_captcha = session.get('captcha')
        stored_captcha_lower = session.get('captcha_lower')
        captcha_time = session.get('captcha_time', 0)
        current_time = datetime.now().timestamp()
        
        print(f"[CAPTCHA] 用户输入: '{captcha}'")
        print(f"[CAPTCHA] 存储的原始: '{stored_captcha}'")
        print(f"[CAPTCHA] 存储的小写: '{stored_captcha_lower}'")
        
        # 验证码验证 - 优先检查是否过期
        if not stored_captcha or not stored_captcha_lower:
            flash('验证码已过期，请刷新页面重试', 'danger')
            current_captcha = get_captcha()
            return render_template('user/login.html', captcha=current_captcha)
        
        if current_time - captcha_time > 300:  # 5分钟过期
            flash('验证码已过期，请刷新页面重试', 'danger')
            current_captcha = get_captcha()
            return render_template('user/login.html', captcha=current_captcha)
        
        if not captcha:
            flash('请输入验证码', 'danger')
            return render_template('user/login.html', captcha=stored_captcha)
        
        if captcha != stored_captcha_lower:
            # 验证码错误时生成新的验证码
            flash('验证码错误，请重试', 'danger')
            current_captcha = generate_captcha()
            return render_template('user/login.html', captcha=current_captcha)
        
        # 检查IP是否在白名单中
        is_whitelisted = False
        try:
            whitelist_entry = IPWhitelist.query.filter_by(ip_address=ip_address, is_active=True).first()
            is_whitelisted = whitelist_entry is not None
            print(f"[WHITELIST DEBUG] 用户登录 - 当前IP: {ip_address}")
            print(f"[WHITELIST DEBUG] 用户登录 - 白名单匹配: {whitelist_entry}")
            print(f"[WHITELIST DEBUG] 用户登录 - 是否白名单: {is_whitelisted}")
        except Exception as e:
            print(f"[WHITELIST DEBUG] 白名单查询失败: {e}")
            # 白名单查询失败不影响登录，默认设为非白名单
        
        # 检查IP是否被封禁（白名单IP也可能被管理员手动封禁）
        ip_ban = IPBan.query.filter_by(ip_address=ip_address).first()
        if ip_ban and ip_ban.is_banned():
            flash('您的IP地址已被封禁，请联系管理员', 'danger')
            log_operation('system', 0, 'IP封禁检测', f'IP: {ip_address} 尝试登录但已被封禁')
            return render_template('user/login.html', captcha=stored_captcha)
        
        user = User.query.filter_by(username=username).first()
        
        # 检查用户是否存在
        if user:
            # 检查账户是否被冻结
            if user.is_frozen:
                # 检查是否是永久冻结（login_attempts >= 10）
                if user.login_attempts >= 10:
                    flash('您的帐户已被永久冻结，请联系管理员', 'danger')
                    log_operation('user', user.id, '永久冻结账户尝试登录', f'IP: {ip_address}')
                    return render_template('user/login.html', captcha=stored_captcha)
                # 检查临时冻结时间是否已过10分钟
                elif user.last_failed_login and datetime.now() - user.last_failed_login > timedelta(minutes=10):
                    # 解冻账户，允许再次尝试登录
                    user.is_frozen = False
                    # 不重置失败次数，保留历史记录
                    db.session.commit()
                else:
                    flash('您的帐户已被冻结，请联系管理员', 'danger')
                    return render_template('user/login.html', captcha=stored_captcha)
            
            # 验证密码
            if user.check_password(password):
                # 登录成功，重置失败次数
                user.login_attempts = 0
                user.last_failed_login = None
                user.is_frozen = False  # 确保账户解冻
                
                # 检查密码哈希算法是否需要升级
                try:
                    from migrate_password_hashes import check_hash_algorithm
                    current_algorithm = check_hash_algorithm(user.password_hash)
                    if current_algorithm == 'pbkdf2:sha256':
                        # 如果用户使用旧算法，更新为新算法
                        from migrate_password_hashes import update_user_password_if_needed
                        update_user_password_if_needed(user, password)
                        flash('密码哈希算法已升级至更高安全级别', 'info')
                except Exception as e:
                    print(f"[PASSWORD HASH DEBUG] 密码哈希算法升级失败: {e}")
                    # 密码哈希升级失败不影响登录
                
                db.session.commit()
                
                # 登录成功，清除验证码
                session.pop('captcha', None)
                session.pop('captcha_lower', None)
                session.pop('captcha_time', None)
                
                session['user_id'] = user.id
                session['username'] = user.username
                session['show_announcement_popup'] = True  # 设置显示公告弹窗标记
                log_operation('user', user.id, '用户登录', f'IP: {ip_address}')
                flash('登录成功', 'success')
                return redirect(url_for('user.index'))
            else:
                # 密码错误，增加失败次数
                user.login_attempts += 1
                user.last_failed_login = datetime.now()
                
                # 如果失败次数达到5次，临时冻结账户
                if user.login_attempts >= 5 and user.login_attempts < 10:
                    user.is_frozen = True
                    # 只有非白名单IP才会被封禁
                    if not is_whitelisted:
                        existing_ban = IPBan.query.filter_by(ip_address=ip_address).first()
                        if not existing_ban:
                            ip_ban = IPBan(
                                ip_address=ip_address,
                                reason=f'用户 {username} 登录失败次数过多',
                                expires_at=datetime.now() + timedelta(minutes=10)
                            )
                            db.session.add(ip_ban)
                        flash('密码错误次数过多，账户和IP已被冻结10分钟', 'danger')
                    else:
                        flash('密码错误次数过多，账户已被冻结10分钟', 'danger')
                # 如果失败次数达到10次，永久冻结账户
                elif user.login_attempts >= 10:
                    user.is_frozen = True
                    # 只有非白名单IP才会被封禁
                    if not is_whitelisted:
                        existing_ban = IPBan.query.filter_by(ip_address=ip_address).first()
                        if not existing_ban:
                            ip_ban = IPBan(
                                ip_address=ip_address,
                                reason=f'用户 {username} 登录失败次数过多',
                                expires_at=None  # 永久封禁
                            )
                            db.session.add(ip_ban)
                        flash('密码错误次数过多，账户和IP已被永久冻结，请联系管理员', 'danger')
                    else:
                        flash('密码错误次数过多，账户已被永久冻结，请联系管理员', 'danger')
                else:
                    flash(f'用户名或密码错误，还有{max(0, 5 - user.login_attempts)}次机会', 'danger')
                
                db.session.commit()
                # 密码错误时生成新的验证码
                current_captcha = generate_captcha()
                return render_template('user/login.html', captcha=current_captcha)
        else:
            # 检查IP是否已被封禁
            existing_ban = IPBan.query.filter_by(ip_address=ip_address).first()
            if existing_ban and existing_ban.is_banned():
                flash('您的IP地址已被封禁，请联系管理员', 'danger')
                return render_template('user/login.html', captcha=stored_captcha)
            
            # 记录登录失败尝试
            log_operation('system', 0, '登录失败', f'IP: {ip_address}, 用户名: {username}')
            flash('用户名或密码错误', 'danger')
            # 用户不存在时生成新的验证码
            current_captcha = generate_captcha()
            return render_template('user/login.html', captcha=current_captcha)
    
    # GET请求时获取验证码（如果存在且未过期则使用现有验证码）
    captcha = get_captcha()
    return render_template('user/login.html', captcha=captcha)


@user_bp.route('/logout')
@user_login_required
def logout():
    """用户退出"""
    user_id = session.get('user_id')
    log_operation('user', user_id, '用户退出')
    session.pop('user_id', None)
    session.pop('username', None)
    flash('已退出登录', 'info')
    return redirect(url_for('user.login'))

@user_bp.route('/debug-session')
def debug_session():
    """调试路由：查看session内容"""
    # 生产环境禁止暴露调试接口，避免泄露敏感信息
    if not current_app.debug:
        return {'error': 'Not Found'}, 404
    captcha = session.get('captcha')
    captcha_lower = session.get('captcha_lower')
    captcha_time = session.get('captcha_time')
    current_time = datetime.now().timestamp()
    
    # 计算验证码是否过期
    is_expired = False
    if captcha_time:
        is_expired = (current_time - captcha_time) > 300
    
    return {
        'captcha': captcha,
        'captcha_lower': captcha_lower,
        'captcha_time': captcha_time,
        'current_time': current_time,
        'is_expired': is_expired,
        'session_content': dict(session)
    }


@user_bp.route('/')
@user_bp.route('/index')
def index():
    """用户首页"""
    # 获取最新失物信息（审核通过的）
    latest_lost_items = LostItem.query.filter_by(status='approved').order_by(
        db.desc(LostItem.created_at)
    ).limit(6).all()
    
    # 获取最新招领信息（审核通过的）
    latest_found_items = FoundItem.query.filter_by(status='approved').order_by(
        db.desc(FoundItem.created_at)
    ).limit(6).all()
    
    # 获取系统公告
    announcements = Announcement.query.order_by(
        db.desc(Announcement.created_at)
    ).limit(5).all()
    
    # 获取最新公告（用于弹窗）
    latest_announcement = None
    show_announcement_popup = False
    if 'user_id' in session:
        # 只在用户登录时显示弹窗
        if session.get('show_announcement_popup', False):
            latest_announcement = Announcement.query.order_by(
                db.desc(Announcement.priority),
                db.desc(Announcement.created_at)
            ).first()
            show_announcement_popup = True
            session.pop('show_announcement_popup', None)  # 显示后清除标记
    
    # 统计数据
    total_lost_items = LostItem.query.filter_by(status='approved').count()
    total_found_items = FoundItem.query.filter_by(status='approved').count()
    total_claims = Claim.query.count()
    total_users = User.query.count()
    
    return render_template('user/index.html', 
                         latest_lost_items=latest_lost_items,
                         latest_found_items=latest_found_items,
                         announcements=announcements,
                         latest_announcement=latest_announcement,
                         show_announcement_popup=show_announcement_popup,
                         total_lost_items=total_lost_items,
                         total_found_items=total_found_items,
                         total_claims=total_claims,
                         total_users=total_users)


@user_bp.route('/lost-items')
def lost_items():
    """失物信息列表"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'latest')
    
    query = LostItem.query.filter_by(status='approved')
    
    # 搜索
    if search:
        query = query.filter(
            db.or_(
                LostItem.title.like(f'%{search}%'),
                LostItem.description.like(f'%{search}%')
            )
        )
    
    # 分类筛选
    if category:
        query = query.filter_by(category=category)
    
    # 排序
    if sort == 'latest':
        query = query.order_by(db.desc(LostItem.created_at))
    elif sort == 'oldest':
        query = query.order_by(LostItem.created_at)
    
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    
    # 获取所有分类
    categories = db.session.query(LostItem.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('user/lost_items.html', 
                         pagination=pagination,
                         search=search,
                         category=category,
                         sort=sort,
                         categories=categories)


@user_bp.route('/found-items')
def found_items():
    """招领信息列表"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'latest')
    
    query = FoundItem.query.filter_by(status='approved')
    
    # 搜索
    if search:
        query = query.filter(
            db.or_(
                FoundItem.title.like(f'%{search}%'),
                FoundItem.description.like(f'%{search}%')
            )
        )
    
    # 分类筛选
    if category:
        query = query.filter_by(category=category)
    
    # 排序
    if sort == 'latest':
        query = query.order_by(db.desc(FoundItem.created_at))
    elif sort == 'oldest':
        query = query.order_by(FoundItem.created_at)
    
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    
    # 获取所有分类
    categories = db.session.query(FoundItem.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('user/found_items.html', 
                         pagination=pagination,
                         search=search,
                         category=category,
                         sort=sort,
                         categories=categories)


@user_bp.route('/lost-items/<int:item_id>')
def lost_item_detail(item_id):
    """失物详情"""
    item = LostItem.query.get_or_404(item_id)
    
    # 获取该失物项目的评论
    try:
        # 直接使用数据库查询获取相关评论
        # 批量预加载评论用户，避免模板逐条触发 N+1 查询
        comments = (
            ThreadComment.query
            .options(selectinload(ThreadComment.user))
            .filter_by(
                lost_item_id=item_id,
                is_deleted=False
            )
            .filter(ThreadComment.status.in_(['active', 'approved']))
            .order_by(ThreadComment.created_at.desc())
            .all()
        )
    except:
        # 如果数据库字段不存在，尝试使用属性方式
        try:
            all_comments = ThreadComment.query.all()
            comments = [comment for comment in all_comments 
                       if getattr(comment, 'lost_item_id', None) == item_id 
                       and not getattr(comment, 'is_deleted', False)
                       and getattr(comment, 'status', 'active') in ['active', 'approved']]
            comments.sort(key=lambda x: x.created_at, reverse=True)
        except:
            comments = []
    
    # 检查是否收藏
    is_favorited = False
    if 'user_id' in session:
        is_favorited = Favorite.query.filter_by(
            user_id=session['user_id'],
            lost_item_id=item_id
        ).first() is not None
    
    return render_template('user/lost_item_detail.html', 
                         item=item,
                         comments=comments,
                         is_favorited=is_favorited)


@user_bp.route('/lost-items/<int:item_id>/add_comment', methods=['POST'])
@user_login_required
def add_lost_item_comment(item_id):
    """为失物信息添加线索/评论"""
    item = LostItem.query.get_or_404(item_id)
    # 直接获取原始内容，不进行任何转义
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('评论内容不能为空', 'danger')
        return redirect(url_for('user.lost_item_detail', item_id=item_id))
    
    # 确保content是普通字符串，使用最直接的方法
    if isinstance(content, str):
        # 已经是字符串，不需要处理
        pass
    else:
        # 不是字符串，转换为字符串
        content = str(content)
    
    user_id = session.get('user_id')
    
    # AI审核内容
    ai_moderation = moderate_and_save_content('thread_comment', content, user_id)
    if not ai_moderation['success']:
        flash(f'评论未通过AI审核: {ai_moderation["reason"]}', 'danger')
        return redirect(url_for('user.lost_item_detail', item_id=item_id))
    
    # 再次确保content是普通字符串
    if not isinstance(content, str):
        content = str(content)
    
    # 创建评论
    comment = ThreadComment(
        user_id=user_id,
        content=content,
        lost_item_id=item_id,  # 直接设置关联的失物ID
        status='approved'  # AI审核通过后直接发布
    )
    
    db.session.add(comment)
    db.session.commit()
    
    log_operation('user', user_id, '添加线索评论', f'在失物信息 {item_id} 下添加评论')
    
    flash('线索评论添加成功', 'success')
    return redirect(url_for('user.lost_item_detail', item_id=item_id))


@user_bp.route('/found-items/<int:item_id>/add_comment', methods=['POST'])
@user_login_required
def add_found_item_comment(item_id):
    """为招领信息添加线索/评论"""
    item = FoundItem.query.get_or_404(item_id)
    # 直接获取原始内容，不进行任何转义
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('评论内容不能为空', 'danger')
        return redirect(url_for('user.found_item_detail', item_id=item_id))
    
    # 确保content是普通字符串，使用最直接的方法
    if isinstance(content, str):
        # 已经是字符串，不需要处理
        pass
    else:
        # 不是字符串，转换为字符串
        content = str(content)
    
    user_id = session.get('user_id')
    
    # AI审核内容
    ai_moderation = moderate_and_save_content('thread_comment', content, user_id)
    if not ai_moderation['success']:
        flash(f'评论未通过AI审核: {ai_moderation["reason"]}', 'danger')
        return redirect(url_for('user.found_item_detail', item_id=item_id))
    
    # 再次确保content是普通字符串
    if not isinstance(content, str):
        content = str(content)
    
    # 创建评论
    comment = ThreadComment(
        user_id=user_id,
        content=content,
        found_item_id=item_id,  # 直接设置关联的招领物ID
        status='approved'  # AI审核通过后直接发布
    )
    
    db.session.add(comment)
    db.session.commit()
    
    log_operation('user', user_id, '添加线索评论', f'在招领信息 {item_id} 下添加评论')
    
    flash('线索评论添加成功', 'success')
    return redirect(url_for('user.found_item_detail', item_id=item_id))


@user_bp.route('/found-items/<int:item_id>')
def found_item_detail(item_id):
    """招领详情"""
    item = FoundItem.query.get_or_404(item_id)
    
    # 获取该招领项目的评论
    try:
        # 直接使用数据库查询获取相关评论
        # 批量预加载评论用户，避免模板逐条触发 N+1 查询
        comments = (
            ThreadComment.query
            .options(selectinload(ThreadComment.user))
            .filter_by(
                found_item_id=item_id,
                is_deleted=False
            )
            .filter(ThreadComment.status.in_(['active', 'approved']))
            .order_by(ThreadComment.created_at.desc())
            .all()
        )
    except:
        # 如果数据库字段不存在，尝试使用属性方式
        try:
            all_comments = ThreadComment.query.all()
            comments = [comment for comment in all_comments 
                       if getattr(comment, 'found_item_id', None) == item_id 
                       and not getattr(comment, 'is_deleted', False)
                       and getattr(comment, 'status', 'active') in ['active', 'approved']]
            comments.sort(key=lambda x: x.created_at, reverse=True)
        except:
            comments = []
    
    # 检查是否收藏
    is_favorited = False
    if 'user_id' in session:
        is_favorited = Favorite.query.filter_by(
            user_id=session['user_id'],
            found_item_id=item_id
        ).first() is not None
    
    return render_template('user/found_item_detail.html', 
                         item=item,
                         comments=comments,
                         is_favorited=is_favorited)


@user_bp.route('/search')
def global_search():
    """全局搜索功能"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        # 如果没有搜索词，重定向到首页
        return redirect(url_for('user.index'))
    
    # 构建搜索查询
    lost_items_query = LostItem.query.filter(
        and_(
            LostItem.status == 'approved',
            db.or_(
                LostItem.title.like(f'%{query}%'),
                LostItem.description.like(f'%{query}%'),
                LostItem.location.like(f'%{query}%')
            )
        )
    )
    
    found_items_query = FoundItem.query.filter(
        and_(
            FoundItem.status == 'approved',
            db.or_(
                FoundItem.title.like(f'%{query}%'),
                FoundItem.description.like(f'%{query}%'),
                FoundItem.location.like(f'%{query}%')
            )
        )
    )
    
    # 分别分页
    lost_pagination = lost_items_query.paginate(
        page=page, per_page=6, error_out=False
    )
    found_pagination = found_items_query.paginate(
        page=page, per_page=6, error_out=False
    )
    
    # 合并结果（只取当前页的数据）
    all_results = []
    all_results.extend([{'type': 'lost', 'item': item} for item in lost_pagination.items])
    all_results.extend([{'type': 'found', 'item': item} for item in found_pagination.items])
    
    # 按创建时间排序
    all_results.sort(key=lambda x: x['item'].created_at, reverse=True)
    
    return render_template('user/search_results.html', 
                         query=query,
                         results=all_results,
                         lost_count=lost_items_query.count(),
                         found_count=found_items_query.count())


@user_bp.route('/lost-items/create', methods=['GET', 'POST'])
@user_login_required
def create_lost_item():
    """发布失物信息"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        lost_time_str = request.form.get('lost_time')
        
        # 验证
        if not all([title, description, category, location]):
            flash('请填写完整信息', 'danger')
            return render_template('user/create_lost_item.html')
        
        try:
            lost_time = datetime.strptime(lost_time_str, '%Y-%m-%d') if lost_time_str else None
        except:
            flash('日期格式错误', 'danger')
            return render_template('user/create_lost_item.html')
        
        # 获取用户ID
        user_id = session.get('user_id')
        
        # AI审核内容
        ai_moderation = moderate_and_save_content('lost_item', description, user_id)
        if not ai_moderation['success']:
            flash(f'内容未通过AI审核: {ai_moderation["reason"]}', 'danger')
            return render_template('user/create_lost_item.html')
        
        # 创建失物信息

        item = LostItem(
            title=title,
            description=description,
            category=category,
            location=location,
            lost_time=lost_time,
            creator_id=user_id,
            status='approved'  # AI审核通过后直接发布
        )
        
        # 处理图片
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                from config import Config
                if allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                    file.save(filepath)
                    item.image = filename
        
        db.session.add(item)
        db.session.commit()
        
        log_operation('user', user_id, '发布失物信息', f'失物: {title}')
        
        flash('失物信息发布成功，等待审核', 'success')
        return redirect(url_for('user.my_lost_items'))
    
    return render_template('user/create_lost_item.html')


@user_bp.route('/found-items/create', methods=['GET', 'POST'])
@user_login_required
def create_found_item():
    """发布招领信息"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        found_time_str = request.form.get('found_time')
        
        # 验证
        if not all([title, description, category, location]):
            flash('请填写完整信息', 'danger')
            return render_template('user/create_found_item.html')
        
        try:
            found_time = datetime.strptime(found_time_str, '%Y-%m-%d') if found_time_str else None
        except:
            flash('日期格式错误', 'danger')
            return render_template('user/create_found_item.html')
        
        # 获取用户ID
        user_id = session.get('user_id')
        
        # AI审核内容
        ai_moderation = moderate_and_save_content('found_item', description, user_id)
        if not ai_moderation['success']:
            flash(f'内容未通过AI审核: {ai_moderation["reason"]}', 'danger')
            return render_template('user/create_found_item.html')
        
        # 创建招领信息

        item = FoundItem(
            title=title,
            description=description,
            category=category,
            location=location,
            found_time=found_time,
            creator_id=user_id,
            status='approved'  # AI审核通过后直接发布
        )
        
        # 处理图片
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                from config import Config
                if allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                    file.save(filepath)
                    item.image = filename
        
        db.session.add(item)
        db.session.commit()
        
        log_operation('user', user_id, '发布招领信息', f'招领: {title}')
        
        flash('招领信息发布成功，等待审核', 'success')
        return redirect(url_for('user.my_found_items'))
    
    return render_template('user/create_found_item.html')


@user_bp.route('/lost-items/<int:item_id>/delete', methods=['POST'])
@user_login_required
def delete_lost_item(item_id):
    """删除自己发布的失物信息"""
    item = LostItem.query.get_or_404(item_id)
    user_id = session.get('user_id')
    
    # 检查是否为该用户创建的物品
    if item.creator_id != user_id:
        flash('您没有权限删除此物品', 'danger')
        return redirect(url_for('user.my_lost_items'))
    
    # 删除相关的认领申请
    Claim.query.filter_by(lost_item_id=item_id).delete()
    
    # 删除相关的评论/线索
    ThreadComment.query.filter_by(lost_item_id=item_id).delete()
    
    # 删除收藏记录
    Favorite.query.filter_by(lost_item_id=item_id).delete()
    
    # 删除物品本身
    db.session.delete(item)
    db.session.commit()
    
    log_operation('user', user_id, '删除失物信息', f'删除失物: {item.title}')
    
    flash('失物信息删除成功', 'success')
    return redirect(url_for('user.my_lost_items'))


@user_bp.route('/found-items/<int:item_id>/delete', methods=['POST'])
@user_login_required
def delete_found_item(item_id):
    """删除自己发布的招领信息"""
    item = FoundItem.query.get_or_404(item_id)
    user_id = session.get('user_id')
    
    # 检查是否为该用户创建的物品
    if item.creator_id != user_id:
        flash('您没有权限删除此物品', 'danger')
        return redirect(url_for('user.my_found_items'))
    
    # 删除相关的认领申请
    Claim.query.filter_by(found_item_id=item_id).delete()
    
    # 删除相关的评论/线索
    ThreadComment.query.filter_by(found_item_id=item_id).delete()
    
    # 删除收藏记录
    Favorite.query.filter_by(found_item_id=item_id).delete()
    
    # 删除物品本身
    db.session.delete(item)
    db.session.commit()
    
    log_operation('user', user_id, '删除招领信息', f'删除招领: {item.title}')
    
    flash('招领信息删除成功', 'success')
    return redirect(url_for('user.my_found_items'))


@user_bp.route('/lost-items/<int:item_id>/favorite', methods=['POST'])
@user_login_required
def favorite_lost_item(item_id):
    """收藏失物信息"""
    user_id = session.get('user_id')
    
    # 检查是否已收藏
    favorite = Favorite.query.filter_by(
        user_id=user_id,
        lost_item_id=item_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'unfavorite'})
    else:
        favorite = Favorite(user_id=user_id, type='lost_item', lost_item_id=item_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'favorite'})


@user_bp.route('/found-items/<int:item_id>/favorite', methods=['POST'])
@user_login_required
def favorite_found_item(item_id):
    """收藏招领信息"""
    user_id = session.get('user_id')
    
    # 检查是否已收藏
    favorite = Favorite.query.filter_by(
        user_id=user_id,
        found_item_id=item_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'unfavorite'})
    else:
        favorite = Favorite(user_id=user_id, type='found_item', found_item_id=item_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'favorite'})


@user_bp.route('/claims/<int:item_id>/<item_type>', methods=['GET', 'POST'])
@user_login_required
def claim_item(item_id, item_type):
    """发起认领申请"""
    # 根据类型获取对应的物品
    if item_type == 'lost':
        item = LostItem.query.get_or_404(item_id)
        item_title = item.title
    elif item_type == 'found':
        item = FoundItem.query.get_or_404(item_id)
        item_title = item.title
    else:
        flash('无效的物品类型', 'danger')
        return redirect(url_for('user.index'))
    
    if request.method == 'POST':
        description = request.form.get('description', '')
        
        if not description:
            flash('请填写认领说明', 'danger')
            return render_template('user/claim_item.html', item=item, item_type=item_type)
        
        user_id = session.get('user_id')
        
        # 检查用户是否已经对该物品提交过认领申请
        existing_claim = Claim.query.filter_by(
            user_id=user_id,
            lost_item_id=item_id if item_type == 'lost' else None,
            found_item_id=item_id if item_type == 'found' else None
        ).first()
        
        if existing_claim:
            flash('您已经对此物品提交过认领申请，请勿重复提交', 'danger')
            return redirect(url_for('user.claim_records'))
        
        # AI审核内容
        ai_moderation = moderate_and_save_content('claim', description, user_id)
        if not ai_moderation['success']:
            flash(f'认领说明未通过AI审核: {ai_moderation["reason"]}', 'danger')
            return render_template('user/claim_item.html', item=item, item_type=item_type)
        
        # 创建认领申请
        claim = Claim(
            description=description,
            status='pending'  # 默认状态为待审核
        )
        
        # 根据类型设置关联字段
        if item_type == 'lost':
            claim.lost_item_id = item_id
        else:
            claim.found_item_id = item_id
            
        claim.user_id = user_id
        
        db.session.add(claim)
        
        # 发送通知给物品发布者
        notification = Notification(
            user_id=item.creator_id,
            type='claim',
            title='收到新认领申请',
            content=f'您的物品《{item_title}》收到了新的认领申请',
            related_id=claim.id,
            redirect_url=url_for(f'user.{item_type}_item_detail', item_id=item_id, _external=True)
        )
        db.session.add(notification)
        
        # 发送通知给申请人，确认申请已提交
        applicant_notification = Notification(
            user_id=user_id,
            type='claim',
            title='认领申请已提交',
            content=f'您的认领申请已提交，物品名称：《{item_title}》',
            related_id=claim.id,
            redirect_url=url_for(f'user.{item_type}_item_detail', item_id=item_id, _external=True)
        )
        db.session.add(applicant_notification)
        
        db.session.commit()
        
        log_operation('user', user_id, '发起认领申请', f'物品: {item_title}')
        
        flash('认领申请已提交', 'success')
        return redirect(url_for('user.claim_records'))
    
    return render_template('user/claim_item.html', item=item, item_type=item_type)


@user_bp.route('/claims')
@user_login_required
def claim_records():
    """认领记录"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    
    pagination = Claim.query.filter_by(user_id=user_id).order_by(
        db.desc(Claim.created_at)
    ).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('user/claim_records.html', pagination=pagination)


@user_bp.route('/profile')
@user_login_required
def profile():
    """个人中心"""
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    # 从 session 中获取身份证号
    if 'id_card_number' in session:
        user.id_card_number = session['id_card_number']
    
    # 统计数据
    lost_count = LostItem.query.filter_by(creator_id=user_id).count()
    found_count = FoundItem.query.filter_by(creator_id=user_id).count()
    claim_count = Claim.query.filter_by(user_id=user_id).count()
    
    stats = {
        'lost_count': lost_count,
        'found_count': found_count,
        'claim_count': claim_count
    }
    
    return render_template('user/profile.html', user=user, stats=stats)


@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@user_login_required
def edit_profile():
    """修改个人信息"""
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    # 从 session 中获取身份证号
    if 'id_card_number' in session:
        user.id_card_number = session['id_card_number']
    
    if request.method == 'POST':
        user.real_name = request.form.get('real_name', '')
        user.phone = request.form.get('phone', '')
        user.student_id = request.form.get('student_id', '')
        user.school = request.form.get('school', '')
        id_card_number = request.form.get('id_card_number', '')
        user.id_card_number = id_card_number
        
        # 将身份证号存储到 session 中
        session['id_card_number'] = id_card_number
        
        db.session.commit()
        
        log_operation('user', user_id, '修改个人信息')
        
        flash('信息修改成功', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('user/edit_profile.html', user=user)


@user_bp.route('/profile/change-password', methods=['GET', 'POST'])
@user_login_required
def change_password():
    """修改密码"""
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not user.check_password(old_password):
            flash('原密码错误', 'danger')
            return render_template('user/change_password.html')
        
        if new_password != confirm_password:
            flash('两次密码不一致', 'danger')
            return render_template('user/change_password.html')
        
        user.set_password(new_password)
        db.session.commit()
        
        log_operation('user', user_id, '修改密码')
        
        flash('密码修改成功，请重新登录', 'success')
        return redirect(url_for('user.logout'))
    
    return render_template('user/change_password.html')


@user_bp.route('/my-lost-items')
@user_login_required
def my_lost_items():
    """我的失物信息"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    
    pagination = LostItem.query.filter_by(creator_id=user_id).order_by(
        db.desc(LostItem.created_at)
    ).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('user/my_lost_items.html', pagination=pagination)


@user_bp.route('/my-found-items')
@user_login_required
def my_found_items():
    """我的招领信息"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    
    pagination = FoundItem.query.filter_by(creator_id=user_id).order_by(
        db.desc(FoundItem.created_at)
    ).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('user/my_found_items.html', pagination=pagination)


@user_bp.route('/items/<int:item_id>/mark-completed/<item_type>', methods=['POST'])
@user_login_required
def mark_item_completed(item_id, item_type):
    """标记物品为已完成/已找回"""
    user_id = session.get('user_id')
    
    if item_type == 'lost':
        item = LostItem.query.get_or_404(item_id)
        if item.creator_id != user_id:
            flash('您没有权限操作此物品', 'danger')
            return redirect(url_for('user.lost_item_detail', item_id=item_id))
        
        item.status = 'completed'
        
        # 发送通知给所有提交过认领申请的用户
        claims = Claim.query.filter_by(lost_item_id=item_id).all()
        for claim in claims:
            notification = Notification(
                user_id=claim.user_id,
                type='claim',
                title='您认领的失物状态更新',
                content=f'您认领的失物《{item.title}》状态已更新为已完成',
                related_id=claim.id,
                redirect_url=url_for('user.lost_item_detail', item_id=item_id, _external=True)
            )
            db.session.add(notification)
        
        db.session.commit()
        
        log_operation('user', user_id, '标记失物为已找回', f'失物: {item.title}')
        flash('失物信息已标记为已找回', 'success')
        
    elif item_type == 'found':
        item = FoundItem.query.get_or_404(item_id)
        if item.creator_id != user_id:
            flash('您没有权限操作此物品', 'danger')
            return redirect(url_for('user.found_item_detail', item_id=item_id))
        
        item.status = 'completed'
        
        # 发送通知给所有提交过认领申请的用户
        claims = Claim.query.filter_by(found_item_id=item_id).all()
        for claim in claims:
            notification = Notification(
                user_id=claim.user_id,
                type='claim',
                title='您认领的招领物品状态更新',
                content=f'您认领的招领物品《{item.title}》状态已更新为已完成',
                related_id=claim.id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        log_operation('user', user_id, '标记招领为已完成', f'招领: {item.title}')
        flash('招领信息已标记为已完成', 'success')
    else:
        flash('无效的物品类型', 'danger')
        
    if item_type == 'lost':
        return redirect(url_for('user.lost_item_detail', item_id=item_id))
    else:
        return redirect(url_for('user.found_item_detail', item_id=item_id))


@user_bp.route('/notifications')
@user_login_required
def notifications():
    """消息通知"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    
    pagination = Notification.query.filter_by(user_id=user_id).order_by(
        db.desc(Notification.created_at)
    ).paginate(page=page, per_page=15, error_out=False)
    
    # 标记为已读
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return render_template('user/notifications.html', pagination=pagination)


@user_bp.route('/api/unread-notifications-count')
@user_login_required
def unread_notifications_count():
    """获取未读通知数量API"""
    user_id = session.get('user_id')
    # 前端会定时轮询；给结果做短缓存，避免每 30s 都打满数据库
    now = time.time()
    ttl_sec = 20
    cache_key = f'unread_count:{user_id}'
    cache = getattr(unread_notifications_count, '_cache', {})
    cached = cache.get(cache_key)
    if cached and cached['expires_at'] > now:
        return jsonify({'unread_count': cached['value']})

    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    # 使用函数属性作为进程内缓存（适用于单进程部署；多进程建议接入 Redis）
    cache[cache_key] = {'expires_at': now + ttl_sec, 'value': unread_count}
    unread_notifications_count._cache = cache
    return jsonify({'unread_count': unread_count})


@user_bp.route('/forum')
def forum():
    """交流论坛"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = ForumPost.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(
            db.or_(
                ForumPost.title.like(f'%{search}%'),
                ForumPost.content.like(f'%{search}%')
            )
        )
    
    # 使用SQLAlchemy内置分页
    pagination = query.order_by(
        db.desc(ForumPost.is_pinned),  # 置顶的在前面
        db.desc(ForumPost.pin_order),  # 按置顶顺序排列
        db.desc(ForumPost.created_at)  # 非置顶的按创建时间排列
    ).paginate(page=page, per_page=15, error_out=False)

    # 论坛列表性能优化：一次性聚合回复数 + 批量预加载作者名
    post_ids = [post.id for post in pagination.items]
    reply_counts = {}
    if post_ids:
        reply_counts = dict(
            ForumReply.query.with_entities(ForumReply.post_id, func.count(ForumReply.id))
            .filter(ForumReply.post_id.in_(post_ids))
            .group_by(ForumReply.post_id)
            .all()
        )

    user_ids = set()
    for post in pagination.items:
        # 管理员/匿名特殊情况不需要查用户表
        if getattr(post, 'is_admin_post', False):
            continue
        if post.user_id and post.user_id not in (0, -1):
            user_ids.add(int(post.user_id))

    user_map = {}
    if user_ids:
        rows = User.query.filter(User.id.in_(user_ids)).all()
        user_map = {u.id: u.username for u in rows if u and u.username}

    for post in pagination.items:
        post.reply_count = reply_counts.get(post.id, 0)

        if getattr(post, 'is_admin_post', False) or post.user_id == -1:
            post._author_name = '管理员'
        elif post.user_id and post.user_id != 0:
            uid = int(post.user_id)
            post._author_name = user_map.get(uid) or f'用户{uid}'
        else:
            post._author_name = '匿名用户'

    return render_template('user/forum.html', pagination=pagination, search=search)


@user_bp.route('/forum/post/<int:post_id>')
def forum_post(post_id):
    """帖子详情"""
    # 确保post_id是int类型
    try:
        post_id = int(post_id)
    except (TypeError, ValueError):
        flash('无效的帖子ID', 'danger')
        return redirect(url_for('user.forum'))
    
    # 查询帖子，确保未被删除
    # 使用完整对象以便模板访问所有属性（如created_at等）
    post = ForumPost.query.filter(
        ForumPost.id == post_id,
        ForumPost.is_deleted == 0
    ).first()
    if not post:
        flash('帖子不存在或已删除', 'warning')
        return redirect(url_for('user.forum'))

    # 预计算帖子作者名：避免模板访问 `post.author_name` 时触发额外查询
    if getattr(post, 'is_admin_post', False) or post.user_id == -1:
        post._author_name = '管理员'
    elif post.user_id and post.user_id != 0:
        author_user = User.query.filter_by(id=post.user_id).first()
        post._author_name = author_user.username if author_user and author_user.username else f'用户{post.user_id}'
    else:
        post._author_name = '匿名用户'

    # 使用ORM查询获取回复 - 直接获取所有回复，不添加is_deleted过滤条件
    # 因为is_deleted字段在数据库中的存储方式可能有问题
    replies = ForumReply.query.filter_by(post_id=post_id).all()

    # 回复作者名批量预加载：避免 N+1 查询
    reply_user_ids = set()
    for reply in replies:
        if getattr(reply, 'admin_reply', 0):
            continue
        if reply.user_id and reply.user_id not in (0, -1):
            reply_user_ids.add(int(reply.user_id))

    reply_user_map = {}
    if reply_user_ids:
        rows = User.query.filter(User.id.in_(reply_user_ids)).all()
        reply_user_map = {u.id: u.username for u in rows if u and u.username}

    for reply in replies:
        if getattr(reply, 'admin_reply', 0):
            reply._cached_author_name = '管理员'
        elif reply.user_id and reply.user_id not in (0, -1):
            uid = int(reply.user_id)
            reply._cached_author_name = reply_user_map.get(uid) or f'用户{uid}'
        else:
            reply._cached_author_name = '匿名用户'
    
    # 检查是否收藏
    is_favorited = False
    if 'user_id' in session:
        is_favorited = Favorite.query.filter_by(
            user_id=session['user_id'],
            post_id=post_id
        ).first() is not None
    
    return render_template('user/forum_post.html', 
                         post=post, 
                         replies=replies,
                         is_favorited=is_favorited)


@user_bp.route('/forum/create', methods=['GET', 'POST'])
@user_login_required
def create_post():
    """发帖"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category', '')
        
        if not all([title, content]):
            flash('请填写完整信息', 'danger')
            return render_template('user/create_post.html')
        
        user_id = session.get('user_id')
        # AI审核内容
        ai_moderation = moderate_and_save_content('post', content, user_id)
        if not ai_moderation['success']:
            flash(f'帖子内容未通过AI审核: {ai_moderation["reason"]}', 'danger')
            return render_template('user/create_post.html')
        
        post = ForumPost(
            title=title,
            content=content,
            category=category,
            user_id=user_id
        )
        
        db.session.add(post)
        db.session.commit()
        
        log_operation('user', user_id, '发帖', f'标题: {title}')
        
        flash('发帖成功', 'success')
        return redirect(url_for('user.forum_post', post_id=post.id))
    
    return render_template('user/create_post.html')


@user_bp.route('/forum/post/<int:post_id>/reply', methods=['POST'])
@user_login_required
def reply_post(post_id):
    """回帖"""
    post = ForumPost.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content:
        flash('请输入回复内容', 'danger')
        return redirect(url_for('user.forum_post', post_id=post_id))
    
    # 转义用户输入，防止XSS攻击
    content = escape(content)
    # 确保content是普通字符串，而不是Markup对象
    if hasattr(content, '__html__'):
        content = content.__html__()
    # 确保content是普通字符串类型
    content = str(content)
    
    # AI审核内容
    user_id = session.get('user_id')
    ai_moderation = moderate_and_save_content('reply', content, user_id)
    if not ai_moderation['success']:
        flash(f'回复内容未通过AI审核: {ai_moderation["reason"]}', 'danger')
        return redirect(url_for('user.forum_post', post_id=post_id))
    
    reply = ForumReply(
        post_id=post_id,
        user_id=user_id,
        content=content,
        is_deleted=False,  # 显式设置未删除状态
        admin_reply=False  # 普通用户回复
    )
    
    db.session.add(reply)
    # 更新帖子的回复计数
    post.reply_count = post.reply_count + 1
    db.session.commit()
    
    # 发送通知给帖子作者（只给普通用户发通知）
    if post.user_id and post.user_id != user_id:
        notification = Notification(
            user_id=post.user_id,
            type='interaction',
            title='收到新回复',
            content=f'您的帖子《{post.title}》收到了新回复',
            related_id=post_id,
            redirect_url=url_for('user.forum_post', post_id=post_id, _external=True)
        )
        db.session.add(notification)
        db.session.commit()
    
    log_operation('user', user_id, '回帖', f'帖子: {post.title}')
    
    flash('回复成功', 'success')
    return redirect(url_for('user.forum_post', post_id=post_id))


@user_bp.route('/forum/reply/<int:reply_id>/delete', methods=['POST'])
@user_login_required
def delete_own_reply(reply_id):
    """删除评论"""
    user_id = session.get('user_id')
    reply = ForumReply.query.get_or_404(reply_id)
    
    # 获取帖子信息
    post = ForumPost.query.get_or_404(reply.post_id)
    
    # 检查权限：用户可以删除自己的评论，帖子作者可以删除自己帖子下的所有评论
    if reply.user_id != user_id and post.user_id != user_id:
        # 检查是否是管理员
        if 'admin_id' not in session:
            flash('您没有权限删除此评论', 'danger')
            return redirect(url_for('user.forum_post', post_id=reply.post_id))
    
    # 软删除评论
    reply.is_deleted = True
    
    # 更新帖子的回复计数
    if post.reply_count > 0:
        post.reply_count = post.reply_count - 1
    
    db.session.commit()
    
    log_operation('user', user_id, '删除评论', f'删除了帖子 {post.title} 下的评论')
    
    flash('评论已删除', 'success')
    return redirect(url_for('user.forum_post', post_id=reply.post_id))


@user_bp.route('/forum/post/<int:post_id>/delete', methods=['POST'])
@user_login_required
def delete_own_post(post_id):
    """删除自己的帖子"""
    user_id = session.get('user_id')
    post = ForumPost.query.get_or_404(post_id)
    
    if post.user_id != user_id:
        flash('无权操作', 'danger')
        return redirect(url_for('user.forum'))
    
    post.is_deleted = True
    db.session.commit()
    
    log_operation('user', user_id, '删除帖子', f'帖子ID: {post_id}')
    
    flash('帖子已删除', 'success')
    return redirect(url_for('user.forum'))


@user_bp.route('/forum/post/<int:post_id>/favorite', methods=['POST'])
@user_login_required
def favorite_post(post_id):
    """收藏帖子"""
    user_id = session.get('user_id')
    
    favorite = Favorite.query.filter_by(
        user_id=user_id,
        post_id=post_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'unfavorite'})
    else:
        favorite = Favorite(user_id=user_id, type='post', post_id=post_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'favorite'})


@user_bp.route('/favorites')
@user_login_required
def favorites():
    """我的收藏"""
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    fav_type = request.args.get('type', 'lost_item')
    
    # 根据收藏类型构建查询
    query = Favorite.query.filter_by(user_id=user_id)
    if fav_type == 'lost_item':
        query = query.filter(Favorite.lost_item_id.isnot(None))
    elif fav_type == 'found_item':
        query = query.filter(Favorite.found_item_id.isnot(None))
    elif fav_type == 'post':
        query = query.filter(Favorite.post_id.isnot(None))
    
    pagination = query.order_by(db.desc(Favorite.created_at)).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('user/favorites.html', pagination=pagination, fav_type=fav_type)