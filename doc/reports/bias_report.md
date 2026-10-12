# Đánh giá LLM Judge Phase B

Nhóm: SKUNN

Người phụ trách: Nguyễn Khánh Sơn — 2A202602388

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T05:03:33.620156+00:00.
Models generation/judge: generation=[] (50/50 answers là `extractive_fallback`, xem lưu ý cuối) / judge=[gpt-4o-mini qua OpenRouter].

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

| id | winner_pass1 | scores_pass1 (A/B) | winner_pass2 (đã quy về A/B gốc) | scores_pass2 (A/B) | final | consistent |
|---|---|---|---|---|---|---|
| 1 | B | 0.8 / 1.0 | A | 1.0 / 0.7 | tie | False |
| 5 | A | 0.7 / 0.2 | A | 0.6 / 0.2 | A | True |
| 12 | A | 1.0 / 0.5 | A | 1.0 / 0.7 | A | True |
| 21 | A | 1.0 / 0.8 | B | 0.6 / 1.0 | tie | False |
| 41 | A | 1.0 / 0.0 | A | 1.0 / 0.2 | A | True |

Reasoning (rút gọn): id 1 — lượt 1 chọn B vì "chính xác và đầy đủ về số ngày nghỉ khi kết hôn", lượt 2 (đảo) chọn nội dung pipeline vì "chi tiết hơn, có nguồn"; id 5 — cả hai lượt chê cả hai đáp án nhưng vẫn chọn A; id 12, 41 — cả hai lượt nhất quán chọn A theo đúng reference (thưởng Tết, phép năm v2024); id 21 — lượt 1 chọn A ("chi tiết hơn về phép năm + lương Senior"), lượt 2 đổi sang B.

Position bias count/rate: 2 / 0.4 (2/5 cặp không nhất quán: id 1 và 21).
Verbosity win rate: 1.0; decisive cases: 3 (cả 3 case A thắng thì A đều dài hơn B: 230 vs 33, 264 vs 50, 274 vs 37 ký tự).

Diễn giải: 2/5 inconsistent là dấu hiệu mất ổn định theo vị trí, nhưng chưa đủ kết luận nguyên nhân là position bias hệ thống — id 1 hai lượt đều chọn đáp án đứng sau, id 21 hai lượt đều chọn đáp án đứng trước (hướng ngược nhau, mẫu chỉ n=5). Verbosity 1.0 gây lo ngại trên lý thuyết, nhưng bị nhiễu: A (extractive pipeline) luôn dài hơn B gấp 3–7 lần ĐỒNG THỜI reasoning của judge luôn viện dẫn accuracy/completeness theo reference, nên không tách được "thắng vì dài" khỏi "thắng vì đủ ý" với 3 decisive cases. Cách kiểm chứng: thêm cặp mà đáp án đúng ngắn hơn đáp án sai, và tăng số cặp.

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

- Judge duy nhất: gpt-4o-mini (temperature 0, JSON mode) qua OpenRouter; mẫu nhỏ (5 cặp, 10 nhãn) nên κ=1.0 chưa chứng minh judge luôn đúng — khoảng tin cậy với n=10 còn rộng.
- Không có case lệch với human trong lần chạy này; nếu chạy lại có lệch, kiểm chứng bằng cách đọc reference từng case thay vì tin judge tuyệt đối.
- Lưu ý cho cả nhóm: 50/50 answers hiện là `extractive_fallback` (generation_models rỗng trong metadata). Phase B vẫn hợp lệ vì judge so sánh đúng nội dung đã lưu, nhưng nhóm nên cân nhắc chạy lại `setup_answers.py` với LLM để có `generation_mode=llm` cho Phase A/báo cáo trung thực hơn.
