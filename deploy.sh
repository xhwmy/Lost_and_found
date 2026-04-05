#!/bin/bash
set -euo pipefail

# 校园众筹项目自动部署脚本（数据安全版）
# 适用环境：CentOS/RHEL 7+，使用 systemd、firewalld
# 使用方法：sudo ./deploy.sh
# 注意：请确保在运行前已手动修改 app.py 和 nginx.conf（如需）
# 修改说明：移除了 --volumes 参数，避免误删数据库卷
# ==================================================

# ---------- 配置变量（请根据实际情况修改）----------
PROJECT_DIR="/opt/campus_project/campus_crowdfunding"
FLASK_PORT=8000
NGINX_PORT=80
COMPOSE_FILE="docker-compose.yml"          # 如文件名不同请修改
BACKUP_NGINX_CONF=true                      # 是否备份 nginx 配置
AUTO_CLEAN_FILES=false                       # 是否自动删除项目目录下所有文件（谨慎！）
# -------------------------------------------------

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_step() {
    echo -e "${BLUE}>>>${NC} $1"
}

# 检查必要命令是否存在
check_commands() {
    local cmds=("docker" "nginx" "firewall-cmd" "systemctl" "curl")
    for cmd in "${cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "命令 '$cmd' 未找到，请安装后重试。"
            exit 1
        fi
    done
    # 检查 docker compose 插件（新版 docker 命令）
    if ! docker compose version &> /dev/null; then
        log_error "docker compose 插件不可用，请安装或使用旧版 docker-compose。"
        exit 1
    fi
}

# 等待 Flask 应用就绪
wait_for_flask() {
    local url="http://127.0.0.1:$FLASK_PORT"
    log_info "等待 Flask 应用启动（最多 60 秒）..."
    for i in {1..30}; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_info "Flask 应用已就绪"
            return 0
        fi
        sleep 2
    done
    log_error "Flask 应用启动超时，请检查容器日志。"
    return 1
}

# 主函数
main() {
    log_step "开始部署校园众筹项目"

    # 1. 前置检查
    check_commands

    # 2. 进入项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录 $PROJECT_DIR 不存在"
        exit 1
    fi
    cd "$PROJECT_DIR"
    log_info "切换到目录：$PROJECT_DIR"

    # 3. 清理旧容器和镜像（保留数据卷！）
    log_step "步骤1：清理旧容器及镜像（保留数据库卷）"
    if [ -f "$COMPOSE_FILE" ]; then
        log_info "停止并移除旧容器"
        docker compose down || true
    else
        log_warn "未找到 $COMPOSE_FILE，跳过 compose 清理"
    fi

    # 4. 清理旧文件（可选，谨慎使用）
    if [ "$AUTO_CLEAN_FILES" = true ]; then
        log_step "步骤2：清理项目目录下的所有文件"
        read -p "是否确定删除 $PROJECT_DIR 下的所有文件？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "${PROJECT_DIR:?}"/*
            log_info "已清空 $PROJECT_DIR"
        else
            log_warn "跳过文件清理"
        fi
    else
        log_info "跳过自动文件清理（AUTO_CLEAN_FILES=false），请手动确保文件已更新"
    fi

    # 设置目录权限（根据实际情况调整）
    chmod -R 755 "$PROJECT_DIR"
    chown -R root:root "$PROJECT_DIR"
    log_info "权限设置为 755，所有者 root:root"

    # 5. 检查 Docker 和 Nginx 服务状态
    log_step "步骤3：检查基础服务状态"
    log_info "检查 Docker 服务"
    systemctl is-active --quiet docker || { log_error "Docker 未运行"; exit 1; }
    log_info "Docker 运行正常"

    log_info "检查 Nginx 服务"
    systemctl is-active --quiet nginx || { log_error "Nginx 未运行"; exit 1; }
    log_info "Nginx 运行正常"

    # 检查 Nginx 语法（当前配置）
    log_info "检查现有 Nginx 配置语法"
    nginx -t || { log_error "Nginx 配置语法错误，请先手动修复"; exit 1; }

    # 6. 构建并启动容器
    log_step "步骤5：构建并启动 Flask 容器"
    log_info "执行 docker compose up -d --build"
    docker compose up -d --build

    log_info "检查容器状态"
    docker compose ps

    # 显示容器日志（最近20行）
    log_info "容器最新日志："
    docker compose logs --tail=20 campus_app || true

    # 等待 Flask 应用就绪
    wait_for_flask || { log_error "Flask 应用未正常响应，退出部署"; exit 1; }

    # 7. 处理 Nginx 配置
    log_step "步骤6：Nginx 配置检查与重载"
    if [ "$BACKUP_NGINX_CONF" = true ] && [ -f /etc/nginx/nginx.conf ]; then
        backup_file="/etc/nginx/nginx.conf.bak.$(date +%Y%m%d-%H%M%S)"
        cp /etc/nginx/nginx.conf "$backup_file"
        log_info "已备份当前 Nginx 配置至 $backup_file"
    fi

    # 提示用户手动修改配置文件（如需要）
    log_warn "请手动检查/编辑 Nginx 配置文件：vi /etc/nginx/nginx.conf"
    read -p "确认已完成 Nginx 配置修改？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "用户取消部署"
        exit 1
    fi

    # 再次检查语法
    log_info "检查 Nginx 配置语法"
    nginx -t || { log_error "Nginx 配置语法错误，请检查刚才的修改"; exit 1; }

    # 重载 Nginx
    log_info "重载 Nginx 服务"
    systemctl reload nginx

    # 验证端口监听
    log_info "验证端口 $NGINX_PORT 监听状态"
    if netstat -tulpn 2>/dev/null | grep -q ":$NGINX_PORT "; then
        log_info "端口 $NGINX_PORT 已被监听"
    else
        log_warn "端口 $NGINX_PORT 未被监听，请检查 Nginx 配置"
    fi

    # 防火墙放行
    log_info "检查防火墙端口 $NGINX_PORT"
    if firewall-cmd --list-ports | grep -q "$NGINX_PORT/tcp"; then
        log_info "防火墙端口 $NGINX_PORT 已开放"
    else
        log_warn "防火墙端口 $NGINX_PORT 未开放，尝试添加"
        firewall-cmd --add-port="$NGINX_PORT/tcp" --permanent
        firewall-cmd --reload
        log_info "防火墙端口已添加"
    fi

    # 8. 最终提示
    log_step "部署完成"
    echo -e "${GREEN}================================================"
    echo "请务必登录云控制台，确认安全组已放行 $NGINX_PORT 端口（0.0.0.0/0）"
    echo "测试访问： http://你的服务器公网IP "
    echo "查看容器日志：docker compose logs -f campus_app"
    echo "================================================${NC}"
}

# 执行主函数
main "$@"
