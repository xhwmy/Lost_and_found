from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import foreign
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import hashlib
from cryptography.fernet import Fernet
import os

# 初始化扩展
db = SQLAlchemy()

# 全局变量，用于跟踪用户冻结状态
frozen_users = set()

# 敏感数据加密工具类
class EncryptedField:
    _cipher = None
    
    @classmethod
    def get_cipher(cls):
        if cls._cipher is None:
            # 使用固定密钥，实际部署时应从环境变量获取
            key = os.environ.get('FIELD_ENCRYPTION_KEY', 'campus_crowdfunding_field_encryption_key').ljust(32)[:32].encode('utf-8')
            key = hashlib.sha256(key).digest()
            cls._cipher = Fernet(key)
        return cls._cipher
    
    @classmethod
    def encrypt(cls, value):
        if value is None:
            return None
        return cls.get_cipher().encrypt(value.encode('utf-8')).decode('utf-8')
    
    @classmethod
    def decrypt(cls, value):
        if value is None:
            return None
        try:
            return cls.get_cipher().decrypt(value.encode('utf-8')).decode('utf-8')
        except:
            return value

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    school = db.Column(db.String(100))
    phone = db.Column(db.String(50))  # 电话号码
    student_id = db.Column(db.String(50))  # 学号
    real_name = db.Column(db.String(100))  # 真实姓名
    created_at = db.Column(db.DateTime, default=datetime.now)
    login_attempts = db.Column(db.Integer, default=0)  # 登录尝试次数
    last_failed_login = db.Column(db.DateTime)  # 最后一次登录失败时间
    
    # 身份证号（内存存储）
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id_card_number = ''

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_frozen(self):
        """获取账户冻结状态，使用内存集合跟踪"""
        return self.id in frozen_users
            
    @is_frozen.setter
    def is_frozen(self, value):
        """设置账户冻结状态，使用内存集合跟踪"""
        if value:
            frozen_users.add(self.id)
        else:
            frozen_users.discard(self.id)
    

    
    @property
    def is_deleted(self):
        """获取删除状态，兼容数据库字段缺失情况"""
        return False
            
    @is_deleted.setter
    def is_deleted(self, value):
        """设置删除状态，兼容数据库字段缺失情况"""
        pass
    
    @property
    def id_card_number(self):
        """获取身份证号"""
        try:
            return self._id_card_number
        except:
            return ''
            
    @id_card_number.setter
    def id_card_number(self, value):
        """设置身份证号"""
        try:
            self._id_card_number = value
        except:
            pass  # 如果无法设置，忽略错误
    
    def __repr__(self):
        return f'<User {self.username}>'

class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    email = db.Column(db.String(120), unique=True)
    real_name = db.Column(db.String(100))  # 真实姓名
    role = db.Column(db.String(50), default='admin')  # 角色
    # last_login_time = db.Column(db.DateTime)  # 上次登录时间 (暂时注释，因为数据库中可能不存在)
    # is_active = db.Column(db.Boolean, default=True)  # 是否激活 (暂时注释，因为数据库中可能不存在)
    # login_attempts = db.Column(db.Integer, default=0)  # 登录尝试次数 (暂时注释，因为数据库中可能不存在)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def last_login_time(self):
        """获取上次登录时间，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_last_login_time', None)
        except AttributeError:
            return None
            
    @last_login_time.setter
    def last_login_time(self, value):
        """设置上次登录时间，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_last_login_time', value)
        except:
            pass  # 如果无法设置，忽略错误
    
    @property
    def is_active(self):
        """获取激活状态，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_is_active', True)  # 默认为激活状态
        except AttributeError:
            return True  # 默认激活
            
    @is_active.setter
    def is_active(self, value):
        """设置激活状态，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_is_active', value)
        except:
            pass  # 如果无法设置，忽略错误
    
    @property
    def login_attempts(self):
        """获取登录尝试次数，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_login_attempts', 0)  # 默认为0次
        except AttributeError:
            return 0  # 默认0次
            
    @login_attempts.setter
    def login_attempts(self, value):
        """设置登录尝试次数，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_login_attempts', value)
        except:
            pass  # 如果无法设置，忽略错误

    @property
    def is_frozen(self):
        """获取账户冻结状态，使用内存集合跟踪"""
        return self.id in frozen_users
            
    @is_frozen.setter
    def is_frozen(self, value):
        """设置账户冻结状态，使用内存集合跟踪"""
        if value:
            frozen_users.add(self.id)
        else:
            frozen_users.discard(self.id)

    def __repr__(self):
        return f'<Admin {self.username}>'

class LostItem(db.Model):
    __tablename__ = 'lost_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    lost_time = db.Column(db.DateTime, default=datetime.now)
    image = db.Column(db.String(200))  # 图片路径
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    reject_reason = db.Column(db.Text)  # 驳回原因

    # 关联关系
    creator = db.relationship('User', backref='lost_items')

    def __repr__(self):
        return f'<LostItem {self.title}>'

class FoundItem(db.Model):
    __tablename__ = 'found_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    found_time = db.Column(db.DateTime, default=datetime.now)
    image = db.Column(db.String(200))  # 图片路径
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    reject_reason = db.Column(db.Text)  # 驳回原因

    # 关联关系
    creator = db.relationship('User', backref='found_items')

    def __repr__(self):
        return f'<FoundItem {self.title}>'

class Claim(db.Model):
    __tablename__ = 'claims'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_items.id'))
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_items.id'))
    description = db.Column(db.Text, nullable=False)  # 认领描述
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联关系
    user = db.relationship('User', backref='claims')
    lost_item = db.relationship('LostItem', backref='claims')
    found_item = db.relationship('FoundItem', backref='claims')

    def __repr__(self):
        return f'<Claim {self.id}>'

class ThreadComment(db.Model):
    __tablename__ = 'thread_comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 关联字段
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_items.id'), nullable=True)
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_items.id'), nullable=True) 
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=True)  # 关联帖子ID
    
    # 回复相关字段
    parent_id = db.Column(db.Integer, db.ForeignKey('thread_comments.id'), nullable=True)  # 支持回复的回复
    is_deleted = db.Column(db.Integer, default=0)  # 软删除标记
    status = db.Column(db.String(20), default='active')  # 评论状态
    
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联关系
    user = db.relationship('User', backref='comments')
    
    # 重写__init__方法，确保content是普通字符串
    def __init__(self, *args, **kwargs):
        # 处理content参数，确保它是普通字符串
        if 'content' in kwargs:
            content = kwargs['content']
            # 确保content是普通字符串，防止Markup对象导致的SQL语法错误
            try:
                if hasattr(content, '__html__'):
                    content = content.__html__()
                content = str(content)
                # 确保content不是Markup对象
                if hasattr(content, '__class__') and content.__class__.__name__ == 'Markup':
                    content = str(content)
            except Exception as e:
                print(f"Error converting content to string: {e}")
                content = str(content)
            kwargs['content'] = content
        super().__init__(*args, **kwargs)
    
    @property
    def parent(self):
        """获取父评论，兼容数据库字段缺失情况"""
        try:
            if hasattr(self, '_parent'):
                return self._parent
            elif self.parent_id:
                return ThreadComment.query.get(self.parent_id)
            else:
                return None
        except:
            return None
    
    def get_children(self):
        """获取子评论，兼容数据库字段缺失情况"""
        try:
            # 如果数据库中有parent_id字段，则查询子评论
            return ThreadComment.query.filter_by(parent_id=self.id).all()
        except:
            # 如果没有parent_id字段，返回空列表
            return []






            

            

    def __repr__(self):
        return f'<ThreadComment {self.id}>'

class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), default='lost_item')  # 收藏类型：lost_item, found_item, post
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_items.id'))
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_items.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'))  # 支持帖子收藏
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联关系
    user = db.relationship('User', backref='favorites')
    lost_item = db.relationship('LostItem')
    found_item = db.relationship('FoundItem')
    post = db.relationship('ForumPost')

    def __repr__(self):
        return f'<Favorite {self.id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'claim', 'item_status', 'admin_message' 等
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    related_id = db.Column(db.Integer)  # 关联ID，如认领申请ID、物品ID等
    redirect_url = db.Column(db.String(500))  # 跳转链接
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联关系
    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.id}>'

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'

    # 基础字段
    id = db.Column(db.Integer, primary_key=True)  
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)  
    # author_name = db.Column(db.String(100), nullable=False)  # 匿名发布者名称 (temporarily removed due to DB mismatch)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 关联用户ID
    category = db.Column(db.String(50))  # 分类   
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Integer, default=0)  # 软删除标记

    like_count = db.Column(db.Integer, default=0)  # 点赞数
    reply_count = db.Column(db.Integer, default=0)  # 回复数
    is_pinned = db.Column(db.Boolean, default=False)  # 是否置顶
    pin_order = db.Column(db.Integer, default=0)  # 置顶顺序
    is_admin_post = db.Column(db.Boolean, default=False)  # 是否为管理员发布的帖子
    
    def __init__(self, *args, **kwargs):
        # 处理content参数，确保它是普通字符串
        if 'content' in kwargs:
            content = kwargs['content']
            # 确保content是普通字符串，防止Markup对象导致的SQL语法错误
            try:
                if hasattr(content, '__html__'):
                    content = content.__html__()
                content = str(content)
                # 确保content不是Markup对象
                if hasattr(content, '__class__') and content.__class__.__name__ == 'Markup':
                    content = str(content)
            except Exception as e:
                print(f"Error converting content to string: {e}")
                content = str(content)
            kwargs['content'] = content
        # 处理数据库字段缺失的情况
        super().__init__(*args, **kwargs)
        
    
    
    @property
    def like_count(self):
        """获取点赞数，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_like_count', 0)
        except AttributeError:
            return 0
            
    @like_count.setter
    def like_count(self, value):
        """设置点赞数，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_like_count', value)
        except:
            pass  # 如果无法设置，忽略错误
            
    @property
    def reply_count(self):
        """获取回复数，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_reply_count', 0)
        except AttributeError:
            return 0
            
    @reply_count.setter
    def reply_count(self, value):
        """设置回复数，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_reply_count', value)
        except:
            pass  # 如果无法设置，忽略错误
    

    
    @property
    def author_name(self):
        """获取作者名称，兼容数据库字段缺失情况"""
        try:
            # 如果数据库中有author_name字段，直接返回
            if hasattr(self, '_author_name') and self._author_name:
                return self._author_name
            # 如果是管理员发布的帖子
            if hasattr(self, 'is_admin_post') and self.is_admin_post:
                return '管理员'
            # 特殊处理管理员发布的帖子
            if self.user_id == -1:
                return '管理员'
            # 检查是否有有效的用户ID
            elif self.user_id and self.user_id != 0:
                current_user_id = self.user_id
                try:
                    current_user_id = int(current_user_id)
                except (ValueError, TypeError):
                    # 如果ID格式不正确，返回默认名称
                    return f'用户{self.user_id}'
                
                # 查询对应的用户
                from models import User
                user = User.query.filter_by(id=current_user_id).first()
                
                if user and user.username:
                    return user.username
                else:
                    # 用户不存在或已删除，返回ID形式的用户名
                    return f'用户{current_user_id}'
            else:
                # 如果没有用户ID，说明是匿名帖子，可以根据需要返回默认值
                return '匿名用户'
        except Exception as e:
            # 如果关联用户不存在或出现错误，返回默认名称
            print(f"获取帖子作者异常：{str(e)}")
            if self.user_id:
                return f'用户{self.user_id}'
            return '匿名用户'
    
    def __repr__(self):
        return f'<ForumPost {self.title}>'

class ForumReply(db.Model):
    __tablename__ = 'forum_replies'  # 严格匹配数据库表名
    
    # 只保留数据库中真实存在的字段，字段类型与数据库完全一致
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)  # 数据库是int，模型也是Integer
    user_id = db.Column(db.Integer, nullable=True)  # 允许为None
    content = db.Column(db.Text, nullable=False)
    admin_reply = db.Column(db.Integer, nullable=False, default=0)  # 数据库tinyint(1)，模型Integer
    admin_id = db.Column(db.Integer, nullable=True)  # 数据库存在，允许NULL值
    is_deleted = db.Column(db.Integer, nullable=False, default=0)  # 数据库tinyint(1)，模型Integer
    created_at = db.Column(db.DateTime, default=datetime.now)
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    
    def __init__(self, *args, **kwargs):
        # 处理content参数，确保它是普通字符串
        if 'content' in kwargs:
            content = kwargs['content']
            # 确保content是普通字符串，防止Markup对象导致的SQL语法错误
            try:
                if hasattr(content, '__html__'):
                    content = content.__html__()
                content = str(content)
                # 确保content不是Markup对象
                if hasattr(content, '__class__') and content.__class__.__name__ == 'Markup':
                    content = str(content)
            except Exception as e:
                print(f"Error converting content to string: {e}")
                content = str(content)
            kwargs['content'] = content
        super().__init__(*args, **kwargs)
    
    # 添加关联关系，以便正确获取用户信息
    # user = db.relationship('User', foreign_keys=[user_id], lazy=True)  # 暂时注释，避免启动错误
    
    # 强制兜底author_name，保证正常显示用户名

    
    @property
    def parent_id(self):
        """获取父回复ID，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_parent_id', None)
        except AttributeError:
            return None
            
    @parent_id.setter
    def parent_id(self, value):
        """设置父回复ID，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_parent_id', value)
        except:
            pass  # 如果无法设置，忽略错误
    
    @property
    def parent(self):
        """获取父回复，兼容数据库字段缺失情况"""
        try:
            if self.parent_id:
                return ForumReply.query.filter_by(id=self.parent_id).first()
            return None
        except:
            return None
            
    @parent.setter
    def parent(self, value):
        """设置父回复，兼容数据库字段缺失情况"""
        try:
            if hasattr(value, 'id'):
                self.parent_id = value.id
        except:
            pass  # 如果无法设置，忽略错误
                
    @property
    def is_deleted(self):
        """获取删除状态，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_is_deleted', False)  # 默认未删除
        except AttributeError:
            return False
                
    @is_deleted.setter
    def is_deleted(self, value):
        """设置删除状态，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_is_deleted', value)
        except:
            pass  # 如果无法设置，忽略错误
                
    @property
    def like_count(self):
        """获取点赞数，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_like_count', 0)  # 默认为0
        except AttributeError:
            return 0
                
    @like_count.setter
    def like_count(self, value):
        """设置点赞数，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_like_count', value)
        except:
            pass  # 如果无法设置，忽略错误
        
    @property
    def author_name(self):
        """获取回复作者名称，兼容数据库字段缺失情况"""
        try:
            # 如果数据库中有author_name字段，直接返回
            if hasattr(self, '_author_name') and self._author_name:
                return self._author_name
            # 如果是管理员的回复（通过数据库字段标记）
            is_admin = bool(getattr(self, 'admin_reply', 0))  # 直接转换为布尔值，兼容1/True、0/False
            if is_admin:
                return '管理员'
            # 处理普通用户回复（容错user_id为空/0/不存在）
            if not getattr(self, 'user_id', None) or getattr(self, 'user_id', 0) <= 0:
                return '匿名用户'
            # 查询用户模型（添加异常捕获，避免查询失败导致整个模板报错）
            try:
                # 导入User模型（建议放在函数内，避免循环导入）
                from models import User
                user = User.query.filter_by(id=getattr(self, 'user_id', 0), is_deleted=0).first()
                return user.username if user and getattr(user, 'username', None) else '匿名用户'
            except Exception as e:
                print(f"查询回复作者失败：{str(e)}")
                return '匿名用户'
        except Exception as e:
            # 如果关联用户不存在或出现错误，返回默认名称
            print(f"获取作者名称异常：{str(e)}")
            return '匿名用户'
        
    def __repr__(self):
        return f'<ForumReply {self.id}>'

class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_published = db.Column(db.Boolean, default=True)  # 是否已发布
    priority = db.Column(db.Integer, default=1)  # 优先级，数字越大越重要

    def __repr__(self):
        return f'<Announcement {self.title}>'

class SecurityRule(db.Model):
    __tablename__ = 'security_rules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 规则名称
    rule_type = db.Column(db.String(50), nullable=False)  # 'amount_limit', 'frequency_limit', 'time_limit', 'ip_limit' 等
    rule_config = db.Column(db.Text, nullable=False)  # 规则配置JSON
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<SecurityRule {self.name}>'

class IPBan(db.Model):
    __tablename__ = 'ip_bans'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)  # 支持IPv6
    reason = db.Column(db.Text)
    # Note: banned_at field was removed to match database structure
    expires_at = db.Column(db.DateTime)  # 过期时间，NULL表示永久封禁

    @property
    def is_active(self):
        """获取IP封禁活动状态，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_is_active', True)
        except AttributeError:
            return True
                
    @is_active.setter
    def is_active(self, value):
        """设置IP封禁活动状态，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_is_active', value)
        except:
            pass  # 如果无法设置，忽略错误
        
    @property
    def created_at(self):
        """获取创建时间，返回当前时间作为默认值"""
        return datetime.now()
    
    @property
    def banned_until(self):
        """获取封禁结束时间，兼容模板中使用的字段名"""
        return self.expires_at
    
    def is_banned(self):
        """判断IP是否仍处于封禁状态"""
        # 如果不是活跃的封禁记录，则不认为是被封禁
        if not self.is_active:
            return False
            
        if self.expires_at is None:
            # 如果没有过期时间，则永久封禁        
            return True
        # 如果有过期时间，则检查是否已过期        
        from datetime import datetime
        return datetime.now() < self.expires_at

    def __repr__(self):
        return f'<IPBan {self.ip_address}>'

class OperationLog(db.Model):
    __tablename__ = 'operation_logs'

    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, nullable=False)  # 操作者ID
    operator_type = db.Column(db.String(20), default='admin')  # 操作者类型: admin, user
    operation = db.Column(db.String(100), nullable=False)  # 操作类型
    # target_type = db.Column(db.String(50))  # 目标类型 (暂时注释，因为数据库中可能不存在)
    # target_id = db.Column(db.Integer)  # 目标ID (暂时注释，因为数据库中可能不存在)
    details = db.Column(db.Text)  # 操作详情
    ip_address = db.Column(db.String(45))  # 操作IP
    created_at = db.Column(db.DateTime, default=datetime.now)
    # user_agent = db.Column(db.Text)  # 用户代理信息 (暂时注释，因为数据库中可能不存在)

    @property
    def target_type(self):
        """获取目标类型，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_target_type', None)
        except AttributeError:
            return None
            
    @target_type.setter
    def target_type(self, value):
        """设置目标类型，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_target_type', value)
        except:
            pass  # 如果无法设置，忽略错误

    @property
    def target_id(self):
        """获取目标ID，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_target_id', None)
        except AttributeError:
            return None
            
    @target_id.setter
    def target_id(self, value):
        """设置目标ID，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_target_id', value)
        except:
            pass  # 如果无法设置，忽略错误

    @property
    def user_agent(self):
        """获取用户代理信息，兼容数据库字段缺失情况"""
        try:
            return getattr(self, '_user_agent', None)
        except AttributeError:
            return None
            
    @user_agent.setter
    def user_agent(self, value):
        """设置用户代理信息，兼容数据库字段缺失情况"""
        try:
            setattr(self, '_user_agent', value)
        except:
            pass  # 如果无法设置，忽略错误

    def __repr__(self):
        return f'<OperationLog {self.operation}>'

class IPWhitelist(db.Model):
    __tablename__ = 'ip_whitelist'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, unique=True)  # IP地址，支持IPv4和IPv6
    description = db.Column(db.String(255))  # 描述
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间

    def __repr__(self):
        return f'<IPWhitelist {self.ip_address}>'