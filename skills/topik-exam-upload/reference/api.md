# Route API dùng khi tải đề

Gốc là `$TOPIK_API_URL`. Mọi route gửi `Authorization: Bearer $TOPIK_API_TOKEN`. Thành công trả `{"status": true, "data": …}`, lỗi trả `{"message", "statusCode"}`; `message` là mã (`media_not_in_group`) hoặc mảng câu lỗi. Trường lạ bị từ chối với `400 property X should not exist`. Danh sách đủ route: `GET /docs-json` (OpenAPI).

`scripts/topik.py` gọi sẵn các route dưới đây. Route không có lệnh riêng thì gọi bằng `topik call <METHOD> <path> [--body file.json]`.

| Việc | Route | Lệnh |
|---|---|---|
| Kiểm token | `GET /v1/auth/me` | `whoami` |
| Tìm đề | `GET /v1/admin/exams?q=` | `find-exam` |
| Tạo đề | `POST /v1/admin/exams` `{title, type}` | `create-exam` |
| Tải file (pdf ≤ 50 MB, mp3 ≤ 200 MB, ảnh ≤ 5 MB) | `POST /v1/media` multipart `file` | `upload` |
| Gửi file cho web đọc | `POST /v1/admin/exams/{id}/imports` `{files: [{role, mediaId}]}` | `import` |
| Trạng thái lần nhập | `GET /v1/admin/exams/{id}/imports/latest` | `job` |
| Gắn audio Nghe | `PUT /v1/admin/exams/{id}/sections/{sectionId}/audio` `{audioMediaId}` | `set-audio` |
| Mốc audio | `GET /v1/admin/exams/{id}/sections/{sectionId}/audio-marks` | `audio-marks` |
| Số trang, ảnh trang PDF | `GET /v1/media/{id}/pages`, `GET /v1/media/{id}/pages/{n}` | `pages` |
| Cả đề | `GET /v1/admin/exams/{id}` | `exam`, `text`, `answers` |
| Cờ đang mở | `GET /v1/admin/exams/{id}/flags` | `flags` |
| Đóng cờ | `POST /v1/admin/exams/{id}/flags/{flagId}/resolve` `{resolution}` | `resolve` |
| Sửa nhóm và câu | `PUT /v1/admin/exams/{id}/groups/{groupId}` | `save-group` |
| Chữ trong ảnh | `PATCH /v1/admin/exams/{id}/groups/{groupId}/images/{mediaId}` `{text}` | `image-text` |
| Duyệt nhóm | `POST /v1/admin/exams/{id}/groups/{groupId}/confirm` | `confirm` |
| Còn gì chặn xuất bản | `GET /v1/admin/exams/{id}/checklist` | `checklist` |
| Phiếu chấm câu Viết 53, 54 | `GET/PUT /v1/admin/questions/{id}/writing-guide` | `writing-guide` |

## Vai trò file khi nhập (`role`)

- `booklet`: đề PDF. Gửi trước, một mình. Web đọc hai lần và so nhau.
- `solution`: file đáp án kèm lời thoại, lời giải, bản dịch, bài mẫu. Web lấy bảng đáp án, lời thoại Nghe, lời giải, bản dịch, bài mẫu Viết. Chỉ gửi được sau khi đề PDF đã gắn (`bookletReady`).
- `answer_key`, `script`: khi đáp án hoặc lời thoại là file riêng.

## Sửa nhóm

`PUT /v1/admin/exams/{id}/groups/{groupId}`. Trường bỏ qua giữ nguyên giá trị cũ. Chỉ gửi câu có thay đổi.

```json
{
  "group": {
    "instruction": "다음을 읽고 물음에 답하십시오.",
    "passageText": "… 나는 비로소 <u>집에 쌀이 떨어진 줄 알았고</u> …"
  },
  "questions": [
    {
      "id": "<question id>",
      "options": [
        {"position": 1, "text": "섭섭하다", "mediaId": null},
        {"position": 2, "text": "원만하다", "mediaId": null},
        {"position": 3, "text": "초조하다", "mediaId": null},
        {"position": 4, "text": "든든하다", "mediaId": null}
      ],
      "correctOption": 1
    }
  ]
}
```

- Trường của nhóm: `instruction`, `example` (〈보기〉), `passageText`, `transcript`, `translation`, `imageMediaId`, `patternKey`.
- Trường của câu: `prompt`, `passageText`, `givenSentence`, `labeledItems` (4 mục), `options` (đủ 4, phương án ảnh giữ `mediaId` cũ), `correctOption` (1–4), `acceptedAnswers`, `modelAnswer`, `charMin`, `charMax`, `explanation`, `translation`, `transcript`.
- Gạch chân viết `<u>…</u>`. Chỗ trống viết `(   )`.
- `409 question_has_answers`: đề đã có người làm. Chỉ gặp ở đề đã xuất bản: dừng, báo người dùng.
- Kết quả trả `questions[].errors`: lý do câu chưa duyệt được.

`GET /v1/admin/exams/{id}`: nhóm ở `sections[].items[].question.group`. Trang của nhóm ở `group.sourcePageFrom`, `sourcePageTo`. Ảnh có `imageMedia.text` (chữ trong ảnh) và `imageMedia.sourcePage`. Phương án ảnh ở `options[].media`.

## Mã cờ hay gặp

| Mã | Nghĩa | Cách xem |
|---|---|---|
| `run_mismatch` | Hai lần đọc khác nhau; `suggestion` là lần đọc 2 | So cả hai với ảnh trang |
| `read_only_once` | Nhóm chỉ một lần đọc có | Xem trang của nhóm, sửa nếu sai, rồi đóng cờ |
| `field_conflict` | Lần nhập sau khác nội dung đang có | So với ảnh trang |
| `missing_underline` | Câu hỏi về phần gạch chân mà chưa có `<u>` | Thêm đúng đoạn sách gạch |
| `image_missing`, `image_box` | Thiếu ảnh hoặc khung ảnh lệch | Xem trang; khung ảnh sửa bằng `PATCH …/images/{mediaId}` `{box}` |
| `script_mismatch` | Lời thoại không khớp audio hay đề | Xem trang lời thoại |
| `points_mismatch` | Điểm in khác điểm theo thể thức | Theo thể thức, ghi nhật ký |
| `incomplete_group`, `unit_rejected`, `structure_changed` | Nhóm thiếu câu, không ghi được, đổi cấu trúc | Đọc `message`; không tự sửa được thì ghi "Cần người xem" |
| `model_note` | Ghi chú của mô hình đọc | Đọc, làm theo nếu đúng, rồi `dismissed` hoặc `kept` |

## Mã checklist

`error` chặn xuất bản: `open_flags`, `unconfirmed_group`, `import_running`, `empty_section`, `points_total`, `draft_question`, `writing_ungradable`, `writing_guide_unreviewed`. `warning`: `read_two_missing`, `missing_slot`, `group_missing_audio`, `audio_marks_missing`, `audio_marks_unreviewed`.

`writing_guide_unreviewed` (phiếu chấm 53, 54 chưa duyệt) luôn còn sau khi bạn xong: duyệt phiếu là việc của người, token bị từ chối.

## Giới hạn

- Tải file: 300 lần mỗi 15 phút. `429` kèm `Retry-After`: script tự chờ.
- `403 insufficient_role`: route cần quyền admin, đừng thử vòng.
- `403 api_token_not_allowed`: xuất bản, ẩn, xoá đề. Đó là việc của người.
