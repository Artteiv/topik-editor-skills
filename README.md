# topik-exam-upload

Bộ skill để agent (Claude Code, Codex) tải một đề luyện thi TOPIK từ thư mục PDF và MP3 lên web luyện thi TOPIK qua API. Agent đưa đủ file lên, kiểm chữ trong ảnh và gạch chân, xử lý cờ, duyệt nhóm. **Người xuất bản đề.**

## Cài

Chép thư mục skill vào nơi agent đọc skill:

```bash
# Claude Code
cp -R skills/topik-exam-upload ~/.claude/skills/
# Codex (và agent khác đọc ~/.agents/skills)
cp -R skills/topik-exam-upload ~/.agents/skills/
```

Cần Python 3.10 trở lên. Script chỉ dùng thư viện chuẩn.

## Cấu hình

Admin tạo token API cho tài khoản editor ở trang Token API của web admin, rồi người tải đề đặt:

```bash
export TOPIK_API_URL=https://<api của web>
export TOPIK_API_TOKEN=tpk_...
```

Token không xuất bản, ẩn hay xoá được đề.

## Dùng

Nói với agent, ví dụ: "Tải đề trong thư mục `~/Đề/hot-topik-2020/test-02` lên web, đây là HOT TOPIK đỏ 2020 Đề 02". Agent ghi mọi việc đã làm vào `upload-log.md` trong thư mục đề, rồi báo còn thiếu gì và đã tự quyết gì.

## Thư mục

- `skills/topik-exam-upload/SKILL.md`: quy trình.
- `skills/topik-exam-upload/reference/`: route API, mẫu nhật ký.
- `skills/topik-exam-upload/scripts/topik.py`: client dòng lệnh của API.
- `tests/`: kịch bản thử skill với agent.
