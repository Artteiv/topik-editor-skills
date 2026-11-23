# Mẫu `upload-log.md`

Đặt ở thư mục đề. Bạn viết các mục dưới đây. Script nối thêm dòng `` - <giờ> `METHOD path` → status `` mỗi lần ghi dữ liệu (khi đã đặt `TOPIK_UPLOAD_LOG`). Không chép nội dung đề vào đây.

~~~markdown
# Tải đề: HOT TOPIK ĐỎ 2020 – Đề 01

- Đề: `<exam id>`, TOPIK II, bản nháp
- File: exam.pdf → `<media id>`; listening.mp3 → `<media id>`; answers-transcripts.pdf → `<media id>`
- Lần nhập đề: job `<id>`, đọc 1: 104/104, đọc 2: lỗi `gemini_http_503`
- Đọc lại đề: job `<id>`, đọc 1: 104/104, đọc 2: thành công
- Lần nhập đáp án: job `<id>`, đáp án 100, lời thoại 50, lời giải 104, thiếu: không

## Sửa so với bản web đọc
- Đọc 19–20, đoạn văn: thêm một từ bị bỏ (trang 24)
- Đọc 42, phương án ②: sửa một từ (trang 35)

## Lỗi in đã sửa
- Đọc 14, phương án ③: ký hiệu lặp (trang 22)

## Cờ đã đóng
- run_mismatch, Nghe 30: kept, bản hiện tại khớp trang 9
- missing_underline, Đọc 42: kept, đã thêm gạch chân theo trang 35

## Tự quyết
- Lời giải tự viết: Đọc 3, 7, 12
- Chữ trong ảnh tự chép: Nghe 1–3, Viết 53

## Cần người xem
- Phiếu chấm Viết 53, 54: lấy từ đề in và sách giải (hoặc: tự soạn, không có sách giải), admin duyệt trước khi xuất bản
- Đọc 42: bảng đáp án ghi ②, lời giải cùng sách chọn ①
- Lần đọc 2 lỗi cả hai job (`<id>`, `<id>`), mã `<lỗi>`: hai lần đọc chưa được so, chặn xuất bản. Cần chạy lại nhập đề
- Đọc 37 vẫn trống sau khi đọc lại (trang 30): cần người nhập câu
- Chưa so được chữ với OCR (cờ `ocr_unavailable`): chạy lại nhập đề hoặc người xem

## Lệnh đã ghi dữ liệu
~~~
