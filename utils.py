from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import current_user
from models import OperationLog, db, ThreadComment
from cryptography.fernet import Fernet
import base64
import hashlib
import json
from datetime import datetime, timedelta


def admin_required(f):
    """管理员登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('请先登录管理员账号', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


def user_login_required(f):
    """用户登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('user.login'))
        return f(*args, **kwargs)
    return decorated_function


def log_operation(operator_type, operator_id, operation, details=None, target_type=None, target_id=None):
    """记录操作日志
    
    Args:
        operator_type: 操作者类型 ('admin', 'user', 'system')
        operator_id: 操作者ID
        operation: 操作描述
        details: 详细信息
        target_type: 目标类型
        target_id: 目标ID
    """
    try:
        # 尝试包含所有字段，但如果数据库不支持某些字段，则忽略它们
        try:
            log = OperationLog(
                operator_type=operator_type,
                operator_id=operator_id,
                operation=operation,
                details=details,
                target_type=target_type,
                target_id=target_id,
                ip_address=getattr(request, 'remote_addr', 'unknown'),
                user_agent=getattr(request, 'headers', {}).get('User-Agent', 'unknown')
            )
        except TypeError as te:
            # 如果某些字段不被支持，尝试创建不带这些字段的日志
            print(f"操作日志创建警告 (字段不匹配): {te}")
            log = OperationLog(
                operator_type=operator_type,
                operator_id=operator_id,
                operation=operation,
                details=details,
                ip_address=getattr(request, 'remote_addr', 'unknown'),
                user_agent=getattr(request, 'headers', {}).get('User-Agent', 'unknown')
            )
        
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"日志记录失败: {e}")
        # 发生错误时回滚会话以避免后续操作受影响
        try:
            db.session.rollback()
        except:
            pass  # 如果回滚也失败，忽略错误


def encrypt_data(data, key):
    """加密敏感数据
    
    Args:
        data: 要加密的字符串数据
        key: 加密密钥
    
    Returns:
        str: 加密后的数据，失败时返回None
    """
    try:
        # 使用密钥生成Fernet对象
        key_hash = hashlib.sha256(key.encode()).digest()
        key_b64 = base64.urlsafe_b64encode(key_hash)
        f = Fernet(key_b64)
        
        # 加密数据
        encrypted = f.encrypt(data.encode())
        return encrypted.decode()
    except Exception as e:
        print(f"加密失败: {e}")
        return None


def decrypt_data(encrypted_data, key):
    """解密敏感数据
    
    Args:
        encrypted_data: 已加密的数据
        key: 解密密钥
    
    Returns:
        str: 解密后的数据，失败时返回None
    """
    try:
        # 使用密钥生成Fernet对象
        key_hash = hashlib.sha256(key.encode()).digest()
        key_b64 = base64.urlsafe_b64encode(key_hash)
        f = Fernet(key_b64)
        
        # 解密数据
        decrypted = f.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"解密失败: {e}")
        return None


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def mask_email(email):
    """邮箱部分隐藏，保护用户隐私
    例： example@test.com -> ex****@test.com
    """
    if not email or '@' not in email:
        return email
    
    parts = email.split('@')
    username = parts[0]
    domain = parts[1]
    
    # 如果用户名太短，至少显示1个字符
    if len(username) <= 2:
        masked_username = username[0] + '*'
    else:
        # 显示前2个字符，其余用****替换
        masked_username = username[:2] + '****'
    
    return f"{masked_username}@{domain}"


def mask_phone(phone):
    """手机号部分隐藏
    例：13812345678 -> 138****5678
    """
    if not phone or len(phone) < 7:
        return phone
    
    # 显示前3位和后4位
    return phone[:3] + '****' + phone[-4:]


def get_pagination_params():
    """获取分页参数"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return page, per_page


def moderate_content_ai(content):
    """使用AI模型审核内容，检测不良信息
    
    Args:
        content (str): 待审核的内容
        
    Returns:
        dict: 包含审核结果的字典
            - is_safe (bool): 是否安全
            - reason (str): 不安全的原因
            - confidence (float): 置信度分数
    """
    # 确保content是普通字符串，防止Markup对象导致的问题
    try:
        if hasattr(content, '__html__'):
            content = content.__html__()
        content = str(content)
    except Exception as e:
        print(f"Error converting content to string: {e}")
        content = str(content)
    
    # 这里实现简单的关键词过滤作为示例
    # 在生产环境中，您可以替换为真正的AI审核服务
    
    # 定义敏感词库
    sensitive_keywords = [
        '色情', '暴力', '恐怖', '政治', '反动', '违法', '犯罪', 
        '歧视', '仇恨', '侮辱', '诽谤', '广告', '垃圾', '恶意',
        '赌博', '毒品', '枪支', '弹药', '病毒', '木马', '黑客',
        '诈骗', '虚假', '谣言', '攻击', '骚扰', '低俗', '露骨',
        '色情', '卖淫', '嫖娼', '赌博', '毒品', '枪支', '弹药', '自杀', '自残',
        '血腥', '残忍', '种族', '民族', '宗教', '地域', '性别', '年龄', '歧视',
        '歧视', '仇恨', '煽动', '分裂', '颠覆', '国家', '政府', '领导', '官员', '贪污',
        '腐败', '受贿', '行贿', '权力', '利益', '冲突', '内幕', '丑闻', '爆料', '泄密',
        '泄露', '隐私', '个人', '信息', '骚扰', '跟踪', '威胁', '恐吓', '辱骂', '诅咒',
        '攻击', '人身', '攻击', '造谣', '传谣', '虚假', '不实', '误导', '欺骗', '诈骗',
        '欺诈', '钓鱼', '病毒', '木马', '恶意', '软件', '破解', '盗版', '侵权', '广告',
        '营销', '推广', '引流', '刷屏', '灌水', '灌水', '垃圾', '信息', '无关', '内容',
        '违规', '不当', '低俗', '庸俗', '恶俗', '色情', '裸露', '暴露', '性', '暗示',
        '暧昧', '挑逗', '诱惑', '暴力', '血腥', '恐怖', '残忍', '伤害', '危险', '行为',
        '危险', '物品', '违禁', '管制', '武器', '爆炸', '燃烧', '剧毒', '放射', '腐蚀',
        '有害', '物质', '毒品', '药品', '处方', '医疗', '健康', '咨询', '诊断', '治疗',
        '建议', '偏方', '秘方', '特效', '神奇', '包治', '百病', '神医', '专家', '权威',
        '机构', '认证', '证书', '专利', '商标', '版权', '知识产权', '法律', '法规',
        '规定', '政策', '制度', '条例', '办法', '规则', '准则', '标准', '规范', '要求',
        '义务', '责任', '权利', '权益', '维权', '投诉', '举报', '反馈', '建议', '意见',
        # 添加脏话和不文明用语
        '草泥马', '草你妈', '操你妈', '操你娘', '狗屎', '粪便', '滚蛋', '去死', '混蛋', '王八蛋',
        'sb', 'SB', '傻逼', '煞笔', '沙比', '憨批', '废物', '窝囊废', '蠢货', '笨蛋',
        '恶心', '讨厌', '麻痹', '妈的', '卧槽', '我靠', '靠', '叼你', '屌你', '日你',
        '干你', '滚开', '闭嘴', '放屁', '扯淡', '胡说', '瞎说', '放狗屁', '神经病', '精神病',
        '智障', '弱智', '白痴', '低能', '脑残', '脑瘫', '缺心眼', '没脑子', '二百五', '一根筋',
        '吃屎', '拉屎', '拉粑粑', '拉臭臭', '放屁', '撒尿', '尿尿', '拉尿', '便便',
        '他妈的', '他娘的', '他奶奶的', '他姥姥的', '他爸爸的', '他妈妈的', '他妹妹的', '他哥哥的',
        '老子', '爷们', '龟儿子', '龟孙子', '乌龟', '王八', '乌龟王八蛋', '杂种', '野种', '私生子',
        '婊子', '妓女', '嫖客', '鸭子', '男妓', '女妓', '卖身', '卖肉', '卖淫', '风尘女子',
        '强奸', '轮奸', '强暴', '性侵', '性骚扰', '猥亵', '下流', '无耻', '卑鄙', '下贱',
        '贪婪', '吝啬', '抠门', '小气', '自私', '自利', '损人利己', '忘恩负义', '背信弃义',
        '背叛', '欺骗', '撒谎', '谎言', '假话', '虚伪', '伪君子', '两面派', '墙头草'
    ]
    
    # 去重敏感词库（保留顺序），减少重复命中判断的开销
    sensitive_keywords = list(dict.fromkeys(sensitive_keywords))
    
    # 检查敏感词
    detected_issues = []
    content_lower = content.lower()
    for keyword in sensitive_keywords:
        if keyword in content_lower:
            detected_issues.append(keyword)
    
    # 如果检测到敏感词，返回不安全结果
    if detected_issues:
        return {
            'is_safe': False,
            'reason': f'检测到敏感词汇: {", ".join(detected_issues[:5])}',  # 只显示前5个敏感词
            'confidence': 0.9
        }
    
    # 检查内容长度是否异常
    if len(content) > 2000:  # 增加长度限制
        return {
            'is_safe': False,
            'reason': '内容长度异常，可能包含垃圾信息',
            'confidence': 0.7
        }
    
    # 检查是否包含过多重复字符（垃圾信息特征）
    import re
    repeated_chars = re.findall(r'(.)\1{5,}', content)  # 查找重复6次以上的字符
    if len(repeated_chars) > 3:  # 如果有超过3种重复字符
        return {
            'is_safe': False,
            'reason': '内容包含过多重复字符，可能为垃圾信息',
            'confidence': 0.8
        }
    
    # 检查是否包含过多链接（垃圾信息特征）
    link_patterns = ['http', 'www.', '.com', '.cn', '.org', '.net']
    link_count = sum(content_lower.count(pattern) for pattern in link_patterns)
    if link_count > 5:  # 如果链接相关的词出现超过5次
        return {
            'is_safe': False,
            'reason': '内容包含过多链接，可能为广告或垃圾信息',
            'confidence': 0.8
        }
    
    # 默认认为内容安全
    return {
        'is_safe': True,
        'reason': '内容安全',
        'confidence': 0.95
    }


def moderate_content_advanced_ai(content):
    """高级AI审核功能 - 可扩展为连接真实AI服务
    
    Args:
        content (str): 待审核的内容
        
    Returns:
        dict: 包含审核结果的字典
    """
    # 这个函数可以扩展为连接真实的AI审核服务
    # 如阿里云内容安全、腾讯云内容审核、百度AI内容审核等
    
    # 示例：调用外部API的伪代码
    # try:
    #     import requests
    #     api_url = os.getenv('AI_MODERATION_API_URL')
    #     api_key = os.getenv('AI_MODERATION_API_KEY')
    #     
    #     response = requests.post(api_url, json={
    #         'content': content,
    #         'api_key': api_key
    #     })
    #     
    #     if response.status_code == 200:
    #         result = response.json()
    #         return {
    #             'is_safe': result.get('is_safe', True),
    #             'reason': result.get('reason', '内容安全'),
    #             'confidence': result.get('confidence', 0.9)
    #         }
    # except Exception as e:
    #     print(f'AI审核服务调用失败: {e}')
    #     # 如果AI服务不可用，降级到本地审核
    #     pass
    
    # 降级到本地审核
    return moderate_content_ai(content)


def moderate_and_save_content(content_type, content, creator_id=None, item_id=None):
    """审核并保存内容
    
    Args:
        content_type (str): 内容类型 ('post', 'reply', 'lost_item', 'found_item', 'claim', 'thread_comment')
        content (str): 内容文本
        creator_id (int): 创建者ID
        item_id (int): 项目ID（如果是更新操作）
        
    Returns:
        dict: 审核结果
    """
    from models import db, LostItem, FoundItem, ForumPost, ForumReply, Claim, ThreadComment
    import json
    
    # AI审核内容
    moderation_result = moderate_content_advanced_ai(content)
    
    # 根据内容类型进行处理
    if not moderation_result['is_safe']:
        # 内容不安全，拒绝发布
        return {
            'success': False,
            'reason': moderation_result['reason'],
            'confidence': moderation_result['confidence'],
            'action': 'rejected'
        }
    
    # 内容安全，根据类型决定是否需要人工审核
    if content_type == 'claim':
        # 认领申请需要人工审核
        return {
            'success': True,
            'reason': '内容通过AI审核，等待人工审核',
            'confidence': moderation_result['confidence'],
            'action': 'pending_manual_review'  # 需要人工审核
        }
    else:
        # 其他类型（帖子、回复、失物、招领、线索评论）AI审核通过后即可发布
        return {
            'success': True,
            'reason': '内容通过AI审核',
            'confidence': moderation_result['confidence'],
            'action': 'approved'
        }


def check_risk_rules(rule_type, user_id=None, ip_address=None, amount=None, frequency_data=None):
    """检查风险规则
    
    Args:
        rule_type: 规则类型 (e.g., 'amount_limit', 'frequency_limit', 'time_limit', 'ip_limit')
        user_id: 用户ID
        ip_address: IP地址
        amount: 金额
        frequency_data: 频率相关数据
        
    Returns:
        tuple: (是否通过检查, 风险原因)
    """
    from models import SecurityRule
    import json
    
    # 获取对应类型的活跃规则
    rules = SecurityRule.query.filter_by(rule_type=rule_type, is_active=True).all()
    
    for rule in rules:
        try:
            # 解析规则配置
            config = json.loads(rule.rule_config)
            
            # 根据规则类型进行检查
            if rule_type == 'amount_limit' and amount is not None:
                max_amount = config.get('max_amount', float('inf'))
                if amount > max_amount:
                    return False, f'金额超过限制（最大 {max_amount}）'
                    
            elif rule_type == 'frequency_limit' and frequency_data is not None:
                max_count = config.get('max_count', float('inf'))
                time_window = config.get('time_window', 3600)  # 默认1小时
                if frequency_data.get('count', 0) > max_count:
                    return False, f'操作频率超过限制（{max_count}次/{time_window}秒）'
                    
            elif rule_type == 'time_limit' and frequency_data is not None:
                min_interval = config.get('min_interval', 0)
                last_time = frequency_data.get('last_time')
                current_time = frequency_data.get('current_time')
                if last_time and current_time - last_time < min_interval:
                    return False, f'操作间隔过短（最少 {min_interval}秒）'
                    
            elif rule_type == 'ip_limit' and ip_address is not None:
                blocked_ips = config.get('blocked_ips', [])
                if ip_address in blocked_ips:
                    return False, 'IP地址被限制'
                    
        except Exception as e:
            print(f"Error checking rule {rule.id}: {e}")
            continue
    
    return True, ""
