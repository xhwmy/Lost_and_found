# AI内容审核功能使用指南

## 功能概述
本系统集成了AI内容审核功能，用于自动检测帖子、回复、失物招领信息和认领说明中的不良信息，减少人工审核工作量。

## 审核范围
- 论坛帖子内容
- 论坛回复内容  
- 失物信息描述
- 招领信息描述
- 认领申请说明

## 审核机制

### 1. 本地关键词过滤
系统内置了丰富的敏感词库，涵盖以下类别：
- 政治敏感内容
- 暴力恐怖信息
- 色情低俗内容
- 广告营销信息
- 垃圾信息特征（重复字符、过多链接等）

### 2. 内容特征检测
- 内容长度异常检测
- 重复字符模式检测
- 链接密度检测

## 扩展为真实AI服务

系统预留了接口，可轻松扩展为真实的AI审核服务：

### 阿里云内容安全接入示例
```python
def moderate_content_cloud_ai(content):
    import requests
    import json
    
    # 配置阿里云内容安全API
    url = "https://green-cip.cn-shanghai.aliyuncs.com/green/text/scan"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        "scenes": ["antispam"],
        "tasks": [{
            "content": content
        }]
    }
    
    # 发送请求到阿里云API
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    result = response.json()
    
    # 解析结果
    suggestion = result['data'][0]['results'][0]['suggestion']
    label = result['data'][0]['results'][0]['label']
    
    return {
        'is_safe': suggestion == 'pass',
        'reason': f'检测结果: {suggestion}, 标签: {label}',
        'confidence': 0.9
    }
```

### 腾讯云内容审核接入示例
```python
def moderate_content_tencent_ai(content):
    import requests
    import json
    
    # 配置腾讯云文本内容安全API
    url = "https://tms.tencentcloudapi.com/"
    
    # 构建请求参数
    params = {
        "Action": "TextModeration",
        "Content": content.encode('utf-8').hex(),
        # 其他必要参数...
    }
    
    # 发送请求并解析结果
    # ...
```

## 配置说明

### 环境变量配置
在`.env`文件中添加：
```
AI_MODERATION_API_URL=your_ai_service_url
AI_MODERATION_API_KEY=your_api_key
```

### 敏感词库扩展
可在`utils.py`中的`sensitive_keywords`数组中添加新的敏感词。

## 审核结果处理
- **通过审核**：内容正常发布，状态为待审核或直接发布
- **未通过审核**：拒绝发布，返回具体原因给用户
- **置信度**：系统会返回审核的置信度分数，便于后续分析

## 注意事项
1. 本地审核作为基础防线，建议配合真实AI服务使用
2. 定期更新敏感词库以应对新型违规内容
3. 对于误判情况，建议建立申诉机制
4. 真实AI服务通常收费，需评估成本效益

## 性能优化
- 本地审核响应速度快，不影响用户体验
- 可配置审核缓存机制，避免重复审核相同内容
- 支持批量审核功能（待实现）