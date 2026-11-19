# topik-exam-upload

Bộ skill để agent (Claude Code, Codex) tải một đề luyện thi TOPIK từ thư mục PDF và MP3 lên web luyện thi TOPIK qua API. Agent đưa đủ file lên, kiểm chữ trong ảnh và gạch chân, xử lý cờ, duyệt nhóm. **Người xuất bản đề.**

## Cài

**Windows:** mở PowerShell, chạy một lệnh:

```powershell
iex ((irm https://raw.githubusercontent.com/Artteiv/topik-editor-skills/main/install.ps1) -replace '^\uFEFF')
```

Trong repo thì bấm đúp `install.cmd`. Script hỏi cài cho Claude Code, Codex hay cả hai, chép skill, rồi hỏi địa chỉ API và token và lưu thành biến môi trường của tài khoản (còn sau khi khởi động lại). Chạy lại script để cập nhật skill hoặc đổi token. Xong thì mở lại terminal và ứng dụng agent.

**macOS, Linux:** chạy một lệnh, không cần tải repo:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Artteiv/topik-editor-skills/main/install.sh)
```

Trong repo thì chạy `bash install.sh`. Script làm như bản Windows; biến lưu ở `~/.config/topik/agent.env` (quyền 600), nạp từ `~/.zshenv` (và `~/.bashrc` nếu có). Xong thì mở terminal mới.

**Cài tay:** chép thư mục skill vào nơi agent đọc skill:

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
