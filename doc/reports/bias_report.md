# Đánh giá LLM Judge Phase B

Nhóm: SKUNN

Người phụ trách: Nguyễn Khánh Sơn — 2A202602388

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T09:21:58.776006+00:00.
Models generation/judge: generation=[gpt-4o-mini-2024-07-18] / judge=[gpt-4o-mini].

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

| id | winner_pass1 | scores_pass1 (A/B) | winner_pass2 (đã quy về A/B gốc) | scores_pass2 (A/B) | final | consistent |
|---|---|---|---|---|---|---|
| 1 | B | 0.7 / 1.0 | B | 0.8 / 1.0 | B | True |
| 5 | A | 0.8 / 0.3 | A | 0.7 / 0.2 | A | True |
| 12 | A | 1.0 / 0.7 | A | 1.0 / 0.8 | A | True |
| 21 | B | 0.0 / 1.0 | B | 0.0 / 1.0 | B | True |
| 41 | A | 1.0 / 0.0 | A | 1.0 / 0.0 | A | True |

Reasoning (rút gọn): id 1 — cả hai lượt nhất quán chọn B vì Answer B cung cấp đầy đủ thông tin về việc nghỉ có lương và không trừ vào phép năm; id 5 — cả hai lượt nhất quán chọn A vì A nêu đúng việc cần phê duyệt theo thẩm quyền giá trị đơn hàng (>10 triệu), trong khi B chỉ nêu Giám đốc phòng ban (không đủ thẩm quyền cho 55 triệu); id 12 — cả hai lượt nhất quán chọn A vì A nêu rõ đối tượng nhân viên từ 6 tháng trở lên; id 21 — cả hai lượt nhất quán chọn B vì A là "Không tìm thấy.", B có đầy đủ 18 ngày phép và lương Senior; id 41 — cả hai lượt nhất quán chọn A vì A trả lời đúng 15 ngày theo v2024 hiện hành, B dùng 12 ngày theo v2023 cũ đã hết hiệu lực.

Position bias count/rate: 0 / 0.0 (5/5 cặp hoàn toàn nhất quán giữa 2 lượt hoán đổi).
Verbosity win rate: 0.8; decisive cases: 5 (4/5 case winner dài hơn đối thủ: A thắng và dài hơn ở id 5, 12; B thắng và dài hơn ở id 1, 21; id 41 A thắng dù ngắn hơn: 38 vs 39 ký tự).

Diễn giải: Position bias = 0.0 cho thấy qua kỹ thuật swap-and-average, LLM Judge hoàn toàn ổn định và không bị phụ thuộc vào thứ tự xuất hiện của các phương án trả lời. Verbosity bias đạt 0.8 (4/5 decisive cases đáp án dài hơn thắng), tuy nhiên khi phân tích chi tiết thì ở id 1, 5, 12, 21, đáp án dài hơn đồng thời cũng là đáp án chứa đầy đủ dữ kiện chính xác và điều kiện theo reference hơn (ví dụ id 21 B có dữ kiện trong khi A chỉ là "Không tìm thấy."; id 1 B có điều kiện có lương). Do đó tỷ lệ 0.8 phản ánh độ đầy đủ nội dung (completeness) đi kèm độ dài chứ không phải thiên vị độ dài đơn thuần.

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json;
không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference.
Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

| question_id | nhãn judge | human_label | agree | reasoning judge (rút gọn) |
|---|---|---|---|---|
| 1 | 1 | 1 | yes | Đúng số ngày nghỉ + điều kiện theo reference |
| 5 | 0 | 0 | yes | Sai: phê duyệt đơn >50tr là Tổng Giám đốc, không phải Giám đốc |
| 12 | 1 | 1 | yes | Đúng điều kiện + mức thưởng nhân viên |
| 21 | 1 | 1 | yes | Đúng số ngày phép + khoảng lương Senior |
| 23 | 1 | 1 | yes | Đúng: hoàn trả 25tr vì chưa đủ 1 năm |
| 29 | 0 | 0 | yes | Sai: thiếu phê duyệt Kế toán trưởng |
| 33 | 1 | 1 | yes | Đúng số ngày phép + phụ cấp hàng tháng |
| 41 | 0 | 0 | yes | Sai: dùng chính sách cũ v2023 thay vì v2024 (15 ngày) |
| 46 | 1 | 1 | yes | Đúng: thử việc không được nghỉ phép năm |
| 50 | 0 | 0 | yes | Sai: cho phép VPN cá nhân, chính sách cấm |

Cohen's κ: 1.0.
Observed agreement p_o = 10/10 = 1.0; chance agreement p_e = 0.6*0.6 + 0.4*0.4 = 0.52 (6 human=1, 4 human=0; judge cũng 6/4); κ = (1.0 − 0.52)/(1 − 0.52) = 1.0 — thang Landis-Koch: almost perfect, đạt bonus κ > 0.6.

## Giới hạn và cách dùng judge

- Judge duy nhất: gpt-4o-mini (temperature 0, JSON mode); mẫu 5 cặp pairwise và 10 nhãn binary, dù đạt κ=1.0 nhưng kích thước mẫu còn nhỏ nên khoảng tin cậy của ước lượng còn rộng.
- Không có case lệch với human trong lần chạy này; nếu triển khai thực tế, cần sampling định kỳ để human review lại các ca có độ tự tin thấp hoặc điểm số sát nút.
- Đáp án pipeline (Answer A) được sinh bằng `gpt-4o-mini-2024-07-18` (mode `llm`), khớp hoàn toàn với pipeline RAG thực tế của Phase A. Swap-and-average giúp loại bỏ hoàn toàn position bias (0.0).
