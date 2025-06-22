#!/bin/bash

# 当任何命令失败时，脚本将立即退出。
set -e

# --- 配置 ---
# 存放 wiki 源 markdown 文件的目录
SOURCE_DOCS_DIR="docs/wiki"
# 用于克隆 wiki 仓库的临时目录
TMP_WIKI_DIR="../WebLoginBrute.wiki.tmp"
# wiki 更新的提交信息
COMMIT_MESSAGE="Update wiki from local docs"

echo "🚀 开始发布 Wiki..."

# 1. 获取远程仓库 URL
REMOTE_URL=$(git remote get-url origin)
if [[ -z "$REMOTE_URL" ]]; then
    echo "❌ 错误：无法确定远程 'origin' 仓库的 URL。"
    exit 1
fi

# 2. 构建 Wiki 仓库的 URL
# 将 'https://github.com/user/repo.git' 转换为 'https://github.com/user/repo.wiki.git'
WIKI_URL=$(echo "$REMOTE_URL" | sed 's/\.git$/.wiki.git/')
echo "ℹ️ Wiki 仓库地址: $WIKI_URL"

# 3. 清理上一次可能残留的临时目录
if [ -d "$TMP_WIKI_DIR" ]; then
    echo "🧹 正在删除已存在的临时目录: $TMP_WIKI_DIR"
    rm -rf "$TMP_WIKI_DIR"
fi

# 4. 克隆 Wiki 仓库
echo "📥 正在从 $WIKI_URL 克隆 Wiki 到 $TMP_WIKI_DIR..."
git clone "$WIKI_URL" "$TMP_WIKI_DIR"

# 5. 复制文档文件
echo "📋 正在从 $SOURCE_DOCS_DIR 复制 Markdown 文件到 Wiki 克隆目录..."
cp "$SOURCE_DOCS_DIR"/*.md "$TMP_WIKI_DIR/"

# 6. 进入 Wiki 目录，提交并推送
echo "⬆️ 正在提交并推送到 Wiki..."
cd "$TMP_WIKI_DIR"
# 检查是否有文件变动，如果没有则不执行提交，避免出错
if [[ -z $(git status -s) ]]; then
    echo "✨ 没有检测到任何变更，无需发布。"
else
    git add .
    git commit -m "$COMMIT_MESSAGE"
    git push
fi
cd ..

# 7. 清理临时目录
echo "🗑️ 正在清理临时目录..."
rm -rf "$TMP_WIKI_DIR"

echo "✅ Wiki 发布成功！" 