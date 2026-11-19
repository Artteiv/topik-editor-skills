#!/usr/bin/env bash
# Cài skill topik-exam-upload trên macOS (hoặc Linux) và lưu TOPIK_API_URL, TOPIK_API_TOKEN
# vào ~/.config/topik/agent.env (quyền 600), nạp từ ~/.zshenv (mọi lần chạy zsh, kể cả agent chạy zsh -lc).
# Chạy trong repo: bash install.sh [claude|codex|both]
# Chạy từ GitHub: bash <(curl -fsSL https://raw.githubusercontent.com/Artteiv/topik-editor-skills/main/install.sh)
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
skill="$here/skills/topik-exam-upload"
if [ ! -d "$skill" ]; then
  # Chạy từ GitHub: không có repo cạnh script, tải bản mới nhất của main.
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  echo "Đang tải skill từ GitHub..."
  curl -fsSL https://codeload.github.com/Artteiv/topik-editor-skills/tar.gz/main | tar -xz -C "$tmp"
  skill="$tmp/topik-editor-skills-main/skills/topik-exam-upload"
  [ -d "$skill" ] || { echo "Tải về không thấy thư mục skill." >&2; exit 1; }
fi

agent=${1:-}
if [ -z "$agent" ]; then
  echo "Cài cho agent nào?"
  echo "  1. Claude Code"
  echo "  2. Codex"
  echo "  3. Cả hai"
  read -r -p "Chọn 1, 2 hoặc 3: " choice
  case $choice in 1) agent=claude ;; 2) agent=codex ;; 3) agent=both ;; esac
fi
case $agent in
  claude) targets=("$HOME/.claude/skills") ;;
  codex) targets=("$HOME/.agents/skills") ;;
  both) targets=("$HOME/.claude/skills" "$HOME/.agents/skills") ;;
  *) echo "Lựa chọn không hợp lệ." >&2; exit 1 ;;
esac

for dir in "${targets[@]}"; do
  mkdir -p "$dir"
  rm -rf "$dir/topik-exam-upload"  # thay bản cũ bằng bản mới
  cp -R "$skill" "$dir/"
  echo "Đã chép skill vào $dir/topik-exam-upload"
done

env_file="$HOME/.config/topik/agent.env"
old_url=""; old_token=""
if [ -f "$env_file" ]; then
  old_url=$(set +u; . "$env_file"; echo "${TOPIK_API_URL:-}")
  old_token=$(set +u; . "$env_file"; echo "${TOPIK_API_TOKEN:-}")
fi

prompt="Địa chỉ API (vd https://api.example.com)"
[ -n "$old_url" ] && prompt="$prompt [Enter để giữ $old_url]"
read -r -p "$prompt: " url
url=${url%/}; url=${url:-$old_url}
case $url in http://*|https://*) ;; *) echo "Địa chỉ API phải bắt đầu bằng http:// hoặc https://" >&2; exit 1 ;; esac

read -r -s -p "Token API (tpk_..., không hiện khi gõ; Enter để giữ token cũ): " token; echo
token=${token:-$old_token}
[ -n "$token" ] || { echo "Chưa có token." >&2; exit 1; }
case "$url$token" in *"'"*) echo "Địa chỉ hoặc token không được chứa dấu nháy đơn." >&2; exit 1 ;; esac

mkdir -p "$(dirname "$env_file")"
umask 077
printf "export TOPIK_API_URL='%s'\nexport TOPIK_API_TOKEN='%s'\n" "$url" "$token" >"$env_file"
chmod 600 "$env_file"
echo "Đã lưu TOPIK_API_URL và TOPIK_API_TOKEN vào $env_file"

line='[ -f "$HOME/.config/topik/agent.env" ] && . "$HOME/.config/topik/agent.env"'
for rc in "$HOME/.zshenv" "$HOME/.bashrc"; do
  # .zshenv luôn được thêm (zsh là shell mặc định của macOS; .zshrc không được đọc khi agent chạy lệnh); .bashrc chỉ khi đã có sẵn.
  [ "$rc" = "$HOME/.bashrc" ] && [ ! -f "$rc" ] && continue
  grep -qF "$line" "$rc" 2>/dev/null || { printf '\n# topik-exam-upload\n%s\n' "$line" >>"$rc"; echo "Đã thêm dòng nạp biến vào $rc"; }
done

command -v python3 >/dev/null || echo "Cảnh báo: không thấy python3. Skill cần Python 3.10 trở lên." >&2

echo
echo "Xong. Mở terminal mới (hoặc chạy: . $env_file) và mở lại ứng dụng Claude/Codex để nhận biến."
