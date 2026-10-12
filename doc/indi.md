# INDIVIDUAL — NguyenKhanhSon-2A202602388

Nhóm: SKUNN — K4 Track 3A Day24 Eval-Guard.

## Phần được giao và phần thực tế đã làm

- Được giao sau khi đổi task với Nguyễn Nam Khánh: toàn bộ Phase B (Tasks 5–8) trong `src/phase_b_judge.py`.
- Thực tế đã làm:
  - T5 `pairwise_judge`: gọi LLM qua `config.get_llm_client()` (tương thích OpenRouter `LLM_BASE_URL`), prompt 3 tiêu chí accuracy/completeness/conciseness kèm reference, `temperature=0`, `response_format=json_object`, parse JSON có fallback, chuẩn hóa winner A/B/tie và clamp scores về [0,1].
  - T6 `swap_and_average`: chạy pairwise 2 lượt đảo thứ tự A/B, quy winner/scores lượt 2 về không gian A/B gốc, consensus else tie, trả `JudgeResult` đầy đủ.
  - T7 `cohen_kappa`: công thức tay `(p_o − p_e)/(1 − p_e)`, xử lý edge `p_e == 1` (trả 1.0 nếu đồng thuận tuyệt đối thay vì chia 0).
  - T8 `bias_report`: đếm position inconsistency, verbosity win rate trên decisive cases, interpretation tách dấu hiệu thống kê khỏi kết luận nguyên nhân.
  - Chạy batch live `python scripts/run_experiments.py --phase b --live` → `artifacts/judge_results.json` (5 cặp × 2 lượt + 10 nhãn binary, κ = 1.0).
  - Điền `doc/reports/bias_report.md` từ JSON thật (bảng 5 cặp, bảng 10 nhãn, phép tính κ, giới hạn mẫu nhỏ).

## Bằng chứng

- Commit/PR: branch `Son` (repo `K4-Track-3A-Day24-Eval-Guard`), chứa `src/phase_b_judge.py`, `artifacts/judge_results.json`, `doc/reports/bias_report.md`, `doc/indi.md`.
- Artifacts/reports: `judge_results.json` có 5 pairwise_results, 10 binary_judgments, calibration κ=1.0, pair_sources đúng (`answers_50q.json:answer` / `human_labels_10q.json:model_answer` / `test_set_50q.json:ground_truth`).

## Cách kiểm tra

- Unit mock (offline, không gọi API): `python -m pytest tests/test_phase_b.py -q` → 8/8 passed; cùng `tests/test_report_contracts.py` → 38 passed.
- Live: `python scripts/run_experiments.py --phase b --live` → `Phase B saved to artifacts/`.
- Checker: `python scripts/check_lab.py` → PASS `phase_b_judge.py`, PASS `Phase B artifact`, PASS `doc/reports/bias_report.md` (các FAIL còn lại thuộc Phase A/C và TEAM của thành viên khác).

## Điều đã học

- Pairwise LLM-as-judge phụ thuộc reference và thứ tự trình bày; swap-and-average phát hiện position bias nhưng với n=5 chỉ là dấu hiệu, không phải chứng minh nguyên nhân.
- Nhãn A/B/tie (so sánh 2 candidates) khác nhãn tốt/xấu 0/1 (đánh giá 1 answer theo reference) — không được quy đổi máy móc.
- Cohen κ hiệu chỉnh đồng thuận ngẫu nhiên (p_e từ phân bố nhãn), đọc theo thang Landis-Koch; κ=1.0 trên n=10 vẫn có khoảng tin cậy rộng.
- Verbosity bias bị nhiễu khi đáp án dài đồng thời đầy đủ ý hơn — cần cặp đối chứng (đáp án đúng ngắn) mới tách được.

## Giới hạn/cách xử lý

- Mẫu nhỏ (5 cặp, 10 nhãn, 1 judge model gpt-4o-mini): kết luận bias chỉ ở mức dấu hiệu, đã ghi rõ trong báo cáo.
- 50/50 answers là `extractive_fallback` nên metadata generation rỗng — không thuộc scope Phase B nhưng đã cảnh báo nhóm trong báo cáo.
- Môi trường thiếu `jsonschema` → cài bổ sung; runner tạo `OpenAI()` trần cho binary judge nên phải thêm `OPENAI_BASE_URL` vào `.env` để trỏ OpenRouter; key cũ 401 nên đã thay key mới (`.env` đã gitignore, không commit).

## Nguồn/AI hỗ trợ nếu có

- Dùng AI assistant để implement 4 hàm theo đúng hợp đồng tests; tự kiểm chứng bằng unit tests mock, live run thật và checker — không dùng kết quả mock thay bằng chứng live.
