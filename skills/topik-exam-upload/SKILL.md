---
name: topik-exam-upload
description: Use when asked to upload, import or put a TOPIK practice exam (đề luyện thi, đề TOPIK, HOT TOPIK, 실전모의고사) from a folder of PDF and MP3 files onto the TOPIK practice website through its API with a tpk_ token, or to resume or check such an upload.
---

# Tải đề TOPIK lên web qua API

Web tự đọc đề PDF bằng Gemini và tự đặt mốc audio. Bạn làm ba việc: đưa đủ file lên, kiểm những chỗ server không tự kiểm được (chữ trong ảnh, gạch chân), rồi xử lý cờ, duyệt nhóm cho tới khi chỉ còn bước xuất bản. **Không chép lại đề và không đọc cả đề**: việc đó tốn hàng triệu token mà vẫn sót lỗi. Chỉ mở trang mà một lệnh hay một cờ chỉ tới. **Xuất bản do người làm**: token API bị từ chối xuất bản, ẩn, xoá đề (`403 api_token_not_allowed`), đừng thử.

**Xong khi** và chỉ khi: `topik flags` không còn cờ mở, mọi nhóm đã duyệt, `topik checklist` hết `error`. Cờ hay nhóm nào bạn không tự xử lý được (cần nghe audio, cần sửa trang nguồn, đáp án sách có vẻ sai) thì vẫn được để lại, nhưng mỗi cái phải có một dòng lý do trong mục "Cần người xem". Chưa đạt thì làm tiếp, đừng viết báo cáo. Đề 30 cờ là bình thường: mỗi cờ chỉ cần một ảnh cắt và một quyết định.

Mọi lệnh dưới đây là `python3 <skill>/scripts/topik.py …` (gọi tắt `topik`), với `<skill>` là thư mục chứa file này. Chi tiết route và body: [reference/api.md](reference/api.md).

## 0. Chuẩn bị

1. Cần `TOPIK_API_URL`, `TOPIK_API_TOKEN` trong môi trường. Không in, không ghi token ra file.
2. `topik whoami` phải ra `"role": "editor"`. Lỗi `401` thì dừng, báo người dùng token sai hoặc hết hạn.
3. Mọi file bạn tạo để trong thư mục đề, ở thư mục con `.upload/` (ảnh trang, JSON). Không để ở `/tmp`.
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

Tạo file ở thư mục đề, theo mẫu [reference/upload-log.md](reference/upload-log.md). Ghi ngay id đề khi có. Mỗi quyết định (sửa chữ, đóng cờ, sửa lỗi in, tự viết nội dung) ghi một dòng: câu nào, đổi gì, căn cứ (trang mấy). Người dùng đọc file này để biết bạn đã làm gì.

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

Sau mỗi `job`: `status` phải là `succeeded`. Mỗi lần đọc (`reads`) phải có `doneQuestions` bằng `expectedQuestions`. Lần đọc nào thiếu thì ghi vào nhật ký và mục "Cần người xem" của báo cáo. File đáp án đọc xong có `report` (số đáp án, lời thoại, lời giải đọc được, câu thiếu `missing`): ghi số liệu này vào nhật ký.

## 4. Kiểm chữ trong ảnh, gạch chân và cờ OCR

`topik checks <exam>` liệt kê ba thứ, kèm số trang. Chỉ lưu và xem đúng các trang đó: `topik pages <id đề PDF> --first N --last N --out <đề>/.upload/pages`.

- **`pictures`**: từng ảnh của đề. Ảnh có chữ in (biểu đồ, áp phích, câu Viết 53) mà `has_text` là `false` thì chép chữ vào bằng `topik image-text`. Ảnh chỉ là tranh thì bỏ qua. Chữ và số có in thì chép đúng như in. Biểu đồ không in số trên thanh nhưng có thang chia thì được đọc giá trị theo thang: ghi `약` trước mỗi số và thêm một dòng "(không in số trên biểu đồ, giá trị đọc theo thang)". Không có thang thì không ghi số. `text` đã có số không khớp ảnh (máy đọc tự bịa) thì thay theo luật này. Mỗi ảnh có số ước ghi vào "Cần người xem". Câu Viết có ảnh mà ảnh không có chữ thì máy không chấm được và đề không xuất bản được (`writing_ungradable`).
- **`underlines`**: câu hỏi nhắc "밑줄" hoặc đã có `<u>`. So `underlined` với đoạn sách gạch: thiếu, thừa hay lệch thì sửa bằng `topik save-group`, ghi nhật ký. Câu nói "밑줄" mà danh sách rỗng thì server đã có cờ `missing_underline`: sửa ở đây rồi đóng cờ ở bước 6.

- **`ocr`**: cờ của bước so chữ với OCR. Server đã so chữ đề với chữ in trên trang (Google Document AI, một bộ đọc chữ trên ảnh, không hiểu nghĩa nên không tự sửa chữ).
  - **`ocr_mismatch`**: chữ đề (`exam`) khác chữ OCR (`ocr`) ở một chỗ. `topik crop-flags <exam> --out <đề>/.upload/crops` cắt dòng của mọi cờ trong một lệnh và in mỗi cờ kèm `image`. Xem lần lượt từng ảnh cắt, so với `exam` và `ocr`, quyết định, rồi sang cờ kế. Không mở cả trang khi đã có ảnh cắt. Cờ có `image` rỗng (không có khung) thì mới lưu và xem cả trang `page`.
    - Đề đọc sai: sửa trường `field` bằng `topik save-group` cho đúng chữ in. Lưu xong, nếu chữ mới khớp OCR thì cờ tự đóng (`topik flags` không còn cờ đó). Cờ vẫn mở vì OCR cũng đọc sai một chữ khác trên dòng đó thì đóng `kept`.
    - OCR đọc sai, ảnh cho thấy đề đúng: đóng `kept`.
    - Lỗi in của sách: sửa cho đúng theo quy tắc, rồi đóng `kept` (chữ đã sửa không bao giờ khớp OCR nên cờ không tự đóng). Ghi nhật ký là lỗi in.
  - **`ocr_page_range`**: chữ của nhóm khớp trang khác (`message` ghi khoảng trang) hơn trang nguồn đang ghi. API không sửa được trang nguồn. Xem trang đang ghi và trang trong `message`:
    - Chữ và ảnh của nhóm vẫn đúng với trang in: đóng `kept`, ghi vào "Cần người xem": nhóm câu mấy, trang nguồn ghi sai, trang đúng là bao nhiêu.
    - Chỉ là nhiễu (nhóm đúng là ở trang đang ghi): đóng `dismissed`.
  - **`ocr_unavailable`**: server chưa so được chữ, ví dụ Google lỗi. Không tự đóng, vì cờ này chặn xuất bản để người chạy lại nhập đề. Ghi vào "Cần người xem".

Chỗ sai chữ khác chỉ sửa khi gặp lúc đang xem trang vì một lý do trên, hoặc khi có cờ.

## 5. Đáp án

`topik answers <exam>` so với bảng đáp án in trong file đáp án, đủ mọi câu trắc nghiệm. Lệch thì theo bảng đáp án in, sửa bằng `save-group`, ghi nhật ký. Bảng đáp án có vẻ sai (lời giải cùng sách nói khác) thì **không tự đổi**: giữ bảng đáp án, ghi vào mục "Cần người xem" của báo cáo.

## 6. Cờ

`topik flags <exam>`. Cờ OCR đã xử lý ở bước 4. Các cờ còn lại xử lý **từng cờ một**, mỗi cờ có căn cứ từ ảnh trang hoặc trang đáp án. Không đóng cờ hàng loạt.

| Kết quả | Khi nào |
|---|---|
| `applied` | Dùng bản đề xuất của cờ (`suggestion`), đã đối chiếu là đúng |
| `kept` | Giữ nội dung hiện tại, đã đối chiếu là đúng (hoặc đã tự sửa đúng bằng `save-group`) |
| `dismissed` | Cờ không đúng sự thật (ví dụ báo thiếu gạch chân mà sách không gạch) |

**`structure_changed`**: file chia nhóm khác khung đề (`message` ghi khoảng câu đọc được và khung). Xem trang in của các câu đó:
- Sách chỉ in khác cách trình bày, câu và nội dung vẫn đúng nhóm của khung (ví dụ in lại lời dẫn trên từng câu): đóng `kept`, `--why` ghi trang và cách sách in.
- Nhóm in thật sự khác khung (lời dẫn khác, câu thuộc nhóm khác): không đóng, ghi vào "Cần người xem": câu mấy, sách chia nhóm thế nào.

Đóng cờ bằng `topik resolve <exam> <flag> <kết quả> --why "<căn cứ>"`, ví dụ `--why "ảnh cắt trang 9: OCR đọc sai"`. Script tự ghi mỗi cờ một dòng vào nhật ký. Căn cứ không chép chữ đề. Cờ tự đóng sau `save-group` thì ghi dòng sửa ở mục "Sửa so với bản web đọc".

## 7. Nội dung còn thiếu: hỏi trước khi tự viết

Sau bước 3, xem câu nào còn thiếu lời giải, bản dịch, bài mẫu Viết, chữ trong ảnh không chép được. Nếu còn thiếu thứ bạn tự viết được, **hỏi người dùng một lần**: bạn tự viết, hay họ chuẩn bị tài liệu. Họ đã trả lời trong yêu cầu thì làm theo, không hỏi lại. Nội dung tự viết không gắn nhãn gì. Chỉ ghi số câu và trường vào nhật ký mục "Tự quyết".

## 8. Phiếu chấm câu Viết 53, 54

AI của web chấm bài Viết dựa vào phiếu chấm, nên phiếu phải sát đề. Mỗi câu một phiếu, gồm:
- `subQuestions`: câu hỏi phụ đề bắt trả lời (`s1`, `s2`…);
- `dataPoints`: dữ kiện phải nêu, ví dụ số liệu biểu đồ câu 53 (`d1`, `d2`…).

Tối đa 10 mục mỗi danh sách, mỗi mục tối đa 500 ký tự.

1. Chỉ xem trang của câu 53, 54 và trang lời giải, bài mẫu của hai câu đó. `topik text <exam> --area 쓰기` cho số trang và `question_id`.
2. Câu hỏi phụ lấy từ đề bài in (gạch đầu dòng, câu hỏi con). Dữ kiện câu 53 lấy từ chữ trong biểu đồ: chép từ cùng nguồn với chữ trong ảnh ở bước 4, nhập cả hai. Đối chiếu bài mẫu trong sách giải để không sót ý. **Không thêm ý ngoài đề.**
3. Người dùng báo không có sách giải thì bạn tự soạn phiếu từ đề bài.
4. Ghi file `.upload/guide-53.json`, `.upload/guide-54.json` dạng `{"subQuestions": [{"id": "s1", "text": "…"}], "dataPoints": [{"id": "d1", "text": "…"}]}`, rồi `topik writing-guide <question_id> --body <file>`.
5. Phiếu cần admin duyệt trước khi xuất bản. **Luôn** ghi vào mục "Cần người xem" của báo cáo: phiếu chấm câu 53, 54, lấy từ đâu (đề và sách giải, hay tự soạn).

## 9. Duyệt nhóm và kiểm cuối

1. Nhóm nào không còn cờ mở: `topik confirm <exam> <group>`. Lỗi trả về (`errors`) thì sửa rồi duyệt lại.
2. `topik audio-marks <exam>`: đơn vị nào `status` "cần nghe" thì ghi vào báo cáo. Bạn không nghe được audio, đừng tự sửa mốc.
3. `topik checklist <exam>`: mọi `error` phải hết. `warning` còn lại thì ghi vào báo cáo.

## 10. Báo cáo cho người dùng

Chỉ viết khi đã đạt điều kiện **Xong khi** ở đầu file. Chạy lại `topik flags` và `topik checklist` ngay trước khi viết để chắc.

Viết tiếng Việt, ngắn, theo thứ tự:

1. Id và tên đề, trạng thái (bản nháp, chờ người xuất bản).
2. **Còn thiếu hoặc cần người xem**: việc gì, câu nào, vì sao. Luôn có dòng phiếu chấm câu 53, 54.
3. **Tự quyết**: liệt kê số câu theo từng loại (sửa chữ so với bản web, lỗi in đã sửa, cờ đã đóng, nội dung tự viết). Không kể lại nội dung.
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
| "Để chắc ăn, đọc lại cả đề so với trang" | Tốn hàng triệu token, model mạnh vẫn sai. Chỉ xem trang mà `checks` hay cờ chỉ tới. |
| "Cờ này chắc ổn, đóng hết cho xong" | Mỗi cờ một căn cứ, ghi nhật ký. |
| "Đáp án sách có vẻ sai, sửa luôn" | Ghi vào "Cần người xem", không tự sửa. |
| "Sách in sai, chép y như sách cho trung thành" | Sửa cho đúng (chính tả, ký hiệu lặp, lời dẫn lệch), ghi mục "Lỗi in đã sửa". Đáp án thì không tự sửa. |
| "Còn nhiều cờ quá, ghi 'cần kiểm tra' rồi báo cáo" | Chưa xong. Mỗi cờ: một ảnh cắt hay một trang, một quyết định. Chỉ để lại cờ có lý do bạn không tự xử lý được. |
| "Lưu cả đề ra JSON rồi đọc hết" | Dùng `topik text --numbers` cho đúng câu cần xem. |
