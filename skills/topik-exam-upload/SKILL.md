---
name: topik-exam-upload
description: Use when asked to upload, import or put a TOPIK practice exam (đề luyện thi, đề TOPIK, HOT TOPIK, 실전모의고사) from a folder of PDF and MP3 files onto the TOPIK practice website through its API with a tpk_ token, or to resume or check such an upload.
---

# Tải đề TOPIK lên web qua API

Web tự đọc đề PDF bằng Gemini và tự đặt mốc audio. Bạn làm ba việc: đưa đủ file lên, **làm người đọc thứ hai độc lập** để bắt lỗi của Gemini, rồi xử lý cờ, duyệt nhóm cho tới khi chỉ còn bước xuất bản. **Xuất bản do người làm**: token API bị từ chối xuất bản, ẩn, xoá đề (`403 api_token_not_allowed`), đừng thử.

Mọi lệnh dưới đây là `python3 <skill>/scripts/topik.py …` (gọi tắt `topik`), với `<skill>` là thư mục chứa file này. Chi tiết route và body: [reference/api.md](reference/api.md).

## 0. Chuẩn bị

1. Cần `TOPIK_API_URL`, `TOPIK_API_TOKEN` trong môi trường. Không in, không ghi token ra file.
2. `topik whoami` phải ra `"role": "editor"`. Lỗi `401` thì dừng, báo người dùng token sai hoặc hết hạn.
3. Mọi file bạn tạo để trong thư mục đề, ở thư mục con `.upload/` (ảnh trang, bản chép, JSON). Không để ở `/tmp`.
4. `export TOPIK_UPLOAD_LOG=<thư mục đề>/upload-log.md`: script tự ghi mỗi lệnh ghi dữ liệu vào đó.

## 1. Kiểm tài nguyên trước khi tải

Mở từng file, đừng đoán theo tên. Cần đủ:

| Thứ | TOPIK II | TOPIK I |
|---|---|---|
| Đề PDF | Nghe 1–50, Viết 51–54, Đọc 1–50 (104 câu) | Nghe 1–30, Đọc 31–70 (70 câu) |
| Audio Nghe | một file mp3 cho cả phần Nghe | như trên |
| Đáp án trắc nghiệm | đủ mọi câu trắc nghiệm | như trên |

Lời thoại, lời giải, bài mẫu Viết thường nằm chung file đáp án ("answers", "정답 및 해설"). Thiếu đề, audio hoặc đáp án thì **dừng**, báo người dùng thiếu gì, chưa tải gì.

## 2. Mở nhật ký `upload-log.md`

Tạo file ở thư mục đề, theo mẫu [reference/upload-log.md](reference/upload-log.md). Ghi ngay id đề khi có. Mỗi quyết định (sửa chữ, đóng cờ, giữ lỗi in, tự viết nội dung) ghi một dòng: câu nào, đổi gì, căn cứ (trang mấy). Người dùng đọc file này để biết bạn đã làm gì.

Chạy lại sau khi bị ngắt: đọc `upload-log.md` trước, dùng lại đề đã tạo (`topik find-exam`), đừng tạo đề mới.

## 3. Tải lên

```bash
topik create-exam "HOT TOPIK ĐỎ 2020 – Đề 01" --type topik_2   # giữ id đề, id phần thi
topik upload exam.pdf            # → media id
topik upload listening.mp3
topik upload answers.pdf
topik import <exam> --booklet <id đề PDF>
topik set-audio <exam> <id mp3>  # server tự nghe và đặt mốc audio
topik job <exam> --wait          # chờ đọc xong (vài phút)
topik import <exam> --solution <id file đáp án>
topik job <exam> --wait
```

Sau mỗi `job`: `status` phải là `succeeded`. Mỗi lần đọc (`reads`) phải có `doneQuestions` bằng `expectedQuestions`. Lần đọc nào thiếu thì phần đó chỉ được đọc một lần: bước 4 càng phải kỹ ở đó, và ghi vào nhật ký. File đáp án đọc xong có `report` (số đáp án, lời thoại, lời giải đọc được, câu thiếu `missing`): ghi số liệu này vào nhật ký.

## 4. Chép mù rồi so: bước bắt lỗi chính

Gemini đọc sai ở chỗ khó thấy: đổi đuôi câu, bỏ một từ, thiếu chữ trong ảnh, thiếu hoặc gạch chân nhầm câu. Hai lần đọc của nó có thể cùng sai, nên không có cờ. Cách bắt: bạn tự chép lại chữ của đề **mà không nhìn bản web đã đọc**, rồi để script so.

1. Lưu ảnh trang: `topik pages <id đề PDF> --out <đề>/.upload/pages`.
2. Chép từng khúc khoảng 5–8 trang, khúc nào xong ghi file khúc đó: `.upload/transcript-p<đầu>-<cuối>.json`, theo đúng định dạng [reference/transcript.md](reference/transcript.md). **Chưa chạy `topik text` hay `topik exam` trước khi chép xong cả đề**: thấy bản web rồi thì bản chép không còn độc lập.
3. Gộp các khúc thành `.upload/transcript.json`, rồi chạy `topik diff <exam> .upload/transcript.json`.
4. Với **từng** mục trong `items`: mở lại ảnh trang, phóng to đúng chỗ lệch, quyết định:
   - Bản web sai → sửa bằng `topik save-group` (xem [reference/api.md](reference/api.md#sửa-nhóm)), ghi nhật ký.
   - Bản chép của bạn sai → không làm gì.
   - Sách in sai (chính tả, ký hiệu lặp): giữ đúng bản in, ghi nhật ký mục "Lỗi in".
   - Chỉ khác chỗ đặt chữ (câu hỏi ở trường khác, lời dẫn lặp ở câu hỏi): sửa cho giống cách web xếp ở các nhóm cùng dạng.
5. Chạy lại `diff` tới khi mọi mục còn lại đều là lỗi của bản chép hoặc lỗi in đã ghi.

Kiểm thêm những thứ cả hai bên hay cùng sót:
- **Chữ trong ảnh**: ảnh phương án (Nghe 1–3), biểu đồ, áp phích, câu Viết 53. Ảnh nào có chữ mà `text` trống thì chép vào bằng `topik image-text`. Câu Viết có ảnh mà ảnh không có chữ thì máy không chấm được và đề không xuất bản được (`writing_ungradable`).
- **Gạch chân**: mọi câu hỏi "밑줄 친 부분" phải có `<u>…</u>` đúng đoạn sách gạch.

## 5. Đáp án

`topik answers <exam>` so với bảng đáp án in trong file đáp án, đủ mọi câu trắc nghiệm. Lệch thì theo bảng đáp án in, sửa bằng `save-group`, ghi nhật ký. Bảng đáp án có vẻ sai (lời giải cùng sách nói khác) thì **không tự đổi**: giữ bảng đáp án, ghi vào mục "Cần người xem" của báo cáo.

## 6. Cờ

`topik flags <exam>`. Xử lý **từng cờ một**, mỗi cờ có căn cứ từ ảnh trang hoặc trang đáp án. Không đóng cờ hàng loạt.

| Kết quả | Khi nào |
|---|---|
| `applied` | Dùng bản đề xuất của cờ (`suggestion`), đã đối chiếu là đúng |
| `kept` | Giữ nội dung hiện tại, đã đối chiếu là đúng (hoặc đã tự sửa đúng bằng `save-group`) |
| `dismissed` | Cờ không đúng sự thật (ví dụ báo thiếu gạch chân mà sách không gạch) |

Mỗi cờ ghi một dòng nhật ký: mã cờ, câu, kết quả, căn cứ.

## 7. Nội dung còn thiếu: hỏi trước khi tự viết

Sau bước 3, xem câu nào còn thiếu lời giải, bản dịch, bài mẫu Viết, chữ trong ảnh không chép được. Nếu còn thiếu thứ bạn tự viết được, **hỏi người dùng một lần**: bạn tự viết, hay họ chuẩn bị tài liệu. Họ đã trả lời trong yêu cầu thì làm theo, không hỏi lại. Nội dung tự viết không gắn nhãn gì. Chỉ ghi số câu và trường vào nhật ký mục "Tự quyết".

## 8. Duyệt nhóm và kiểm cuối

1. Nhóm nào đã qua bước 4–6, không còn cờ mở: `topik confirm <exam> <group>`. Lỗi trả về (`errors`) thì sửa rồi duyệt lại.
2. `topik audio-marks <exam>`: đơn vị nào `status` "cần nghe" thì ghi vào báo cáo. Bạn không nghe được audio, đừng tự sửa mốc.
3. `topik checklist <exam>`: mọi `error` phải hết. `warning` còn lại thì ghi vào báo cáo.

## 9. Báo cáo cho người dùng

Viết tiếng Việt, ngắn, theo thứ tự:

1. Id và tên đề, trạng thái (bản nháp, chờ người xuất bản).
2. **Còn thiếu hoặc cần người xem**: việc gì, câu nào, vì sao.
3. **Tự quyết**: liệt kê số câu theo từng loại (sửa chữ so với bản web, lỗi in giữ nguyên, cờ đã đóng, nội dung tự viết). Không kể lại nội dung.
4. Đường dẫn `upload-log.md`.

## Không làm

- Không xuất bản, ẩn, xoá đề. Không gọi route `DELETE`.
- Không dùng trình duyệt hay giao diện web. Chỉ dùng API.
- Không sửa nội dung khi chưa xem ảnh trang tương ứng.
- Không đổi đáp án mà bảng đáp án in không nói vậy.
- Không chép nội dung đề vào log hay báo cáo (có bản quyền). Ghi số câu, id.

## Dấu hiệu đang làm sai

| Ý nghĩ | Thực tế |
|---|---|
| "Gemini đọc hai lần rồi, không cờ là đúng" | Hai lần đọc có thể cùng sai, hoặc một lần bị cụt. Bước 4 là bắt buộc. |
| "Xem bản web trước cho nhanh rồi sửa" | Thấy bản web rồi bạn sẽ đọc theo nó. Chép xong mới so. |
| "Cờ này chắc ổn, đóng hết cho xong" | Mỗi cờ một căn cứ, ghi nhật ký. |
| "Đáp án sách có vẻ sai, sửa luôn" | Ghi vào "Cần người xem", không tự sửa. |
| "Chữ sai chính tả, sửa cho đúng" | Giữ bản in, ghi mục "Lỗi in". |
| "Đề nhiều câu quá, kiểm phần Nghe là đủ" | Chép và so cả ba phần. |
