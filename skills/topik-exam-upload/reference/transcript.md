# Bản chép mù

Mỗi khúc trang một file JSON, gộp lại thành `.upload/transcript.json` để chạy `topik diff`.

```json
{"questions": [
  {"area": "읽기", "number": 23, "page": 26,
   "text": "다음 글을 읽고 물음에 답하십시오.\n어느 날 아침이었다. … <u>나는 비로소 집에 쌀이 떨어진 줄 알았고 얼굴이 화끈거렸다.</u>\n밑줄 친 부분에 나타난 '나'의 심정으로 알맞은 것을 고르십시오.\n① 촌스럽다\n② 쑥스럽다\n③ 미안스럽다\n④ 실망스럽다"}
]}
```

- `area`: `듣기`, `쓰기`, `읽기`. `number`: số câu in trong đề (Đọc đánh lại từ 1).
- `text`, theo thứ tự, mỗi phần một dòng:
  1. dòng lời dẫn của nhóm (sau ※, bỏ `[a~b]` và điểm),
  2. 〈보기〉 nếu có,
  3. đoạn văn chung hoặc chữ trong ảnh chung của nhóm,
  4. đoạn văn hoặc chữ trong ảnh riêng của câu,
  5. dòng câu hỏi,
  6. bốn phương án, mỗi phương án bắt đầu bằng ①②③④ (phương án là ảnh thì chép chữ trong ảnh).
- Câu trong cùng nhóm đều chép đủ phần chung.

Luật chép:

- Chép đúng chữ in: cùng từ, cùng đuôi câu, cùng chính tả, kể cả khi bản in có vẻ sai. Không sửa, không rút gọn, không viết lại cho trơn.
- Gạch chân viết `<u>…</u>`, đúng từ đầu tới cuối đoạn sách gạch. Chỗ trống viết `(   )`.
- Chữ in trong ảnh, biểu đồ, áp phích cũng chép (tiêu đề, nhãn, số, đơn vị).
- Chữ khó đọc thì phóng to đúng chỗ đó trên ảnh trang rồi mới quyết. Không đoán theo nghĩa.
- Nghe: chép phần in trong đề (lời dẫn, câu hỏi, phương án). Không chép lời thoại audio.
- Viết 51–54: chép lời dẫn, đề, chữ trong ảnh. Không chép ví dụ 원고지 in mẫu cách viết.

Script so chữ sau khi bỏ khoảng trắng, dấu câu, ký hiệu ①–④ và chữ 〈보기〉, nên không cần căn đúng xuống dòng hay dấu cách.
