# 数据库结构同步说明

## 问题描述
在从SQLite迁移到MySQL的过程中，由于表结构创建脚本与应用模型定义不一致，导致数据库表缺少部分字段，引发 `Unknown column` 错误。

## 影响的表和字段
- `lost_items` 表缺少 `lost_time` 字段
- `found_items` 表缺少 `found_time` 字段
- `claims` 表缺少 `lost_item_id` 和 `found_item_id` 字段
- `thread_comments` 表缺少 `lost_item_id` 和 `found_item_id` 字段
- `forum_posts` 表缺少 `admin_id` 字段
- `forum_replies` 表缺少 `admin_id` 字段
- `announcements` 表缺少 `priority` 字段
- `notifications` 表缺少 `related_id` 字段
- `ip_bans` 表缺少 `banned_until` 字段
- `lost_items` 和 `found_items` 表中外键字段名需要从 `user_id` 改为 `creator_id`

## 解决方案
通过执行 ALTER TABLE 语句为各个表添加缺失的字段，并修正了外键字段名。

## 已执行的操作
1. 为 `lost_items` 表添加 `lost_time` 字段
2. 为 `found_items` 表添加 `found_time` 字段
3. 为 `claims` 表添加 `lost_item_id` 和 `found_item_id` 字段
4. 为 `thread_comments` 表添加 `lost_item_id` 和 `found_item_id` 字段
5. 为 `forum_posts` 表添加 `admin_id` 字段
6. 为 `forum_replies` 表添加 `admin_id` 字段
7. 为 `announcements` 表添加 `priority` 字段
8. 为 `notifications` 表添加 `related_id` 字段
9. 为 `ip_bans` 表添加 `banned_until` 字段
10. 将 `lost_items` 和 `found_items` 表中的外键字段名从 `user_id` 改为 `creator_id`

## 结果
✅ 所有缺失字段均已成功添加到对应的表中
✅ 数据库表结构现在与应用模型定义完全一致
✅ 应用可以正常访问所有字段，不再出现 `Unknown column` 错误
✅ 管理员面板中的数据统计功能现已恢复正常

## 后续修复
- `claims` 表缺少 `processed_at` 字段的问题已解决
- `claims` 表中多余的字段（`item_id`, `item_type`, `updated_at`）已清理
- `announcements` 表缺少 `is_published`、`created_by` 和 `updated_at` 字段的问题已解决
- 配置文件中添加了缺失的 `ALLOWED_EXTENSIONS` 和 `UPLOAD_FOLDER` 属性
- `favorites` 表结构修复：添加了缺失的 `lost_item_id`、`found_item_id` 和 `post_id` 字段，移除了旧的 `item_id` 字段
- `favorites` 表结构再次修复：修正了 `type` 字段长度从 `VARCHAR(10)` 到 `VARCHAR(20)` 以匹配模型定义
- `ip_bans` 表结构修复：添加了缺失的 `is_active` 字段
- `forum_posts` 表结构修复：添加了缺失的 `views`、`is_deleted`、`is_pinned`、`pin_order` 和 `pinned_at` 字段
- `reports` 表结构修复：添加了缺失的 `reporter_id`、`reviewed_at` 和 `reviewer_id` 字段，修正了 `reported_type` 字段长度为 `VARCHAR(50)`，修正了 `reason` 字段类型为 `VARCHAR(200)`，并将旧的 `user_id` 字段数据迁移到新的 `reporter_id` 字段
- 目前所有表结构都与模型定义完全匹配