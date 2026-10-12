# Blueprint CI/CD cho RAG và guardrails

Phần Phase C: Ngô Đinh Minh Nhật. Đây là đề xuất CI/CD, chưa phải workflow đã triển khai.

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.

Presidio detect/redact CCCD/CMND, điện thoại Việt Nam và các PII có định dạng (email, số điện thoại, thẻ, IBAN, IP). `pii_scan` bỏ các entity dựa trên NER (PERSON/LOCATION/DATE_TIME/NRP) và các mẫu US_* điểm thấp: với model spaCy `en_core_web_lg`, NER gán nhầm PERSON cho cụm tiếng Việt thường, làm lượt live đầu chặn 8/8 clean controls. Yêu cầu dữ liệu của nhân viên khác theo tên do NeMo input xử lý. Request có PII dừng ở Presidio; request còn lại được NeMo kiểm tra phạm vi chính sách, jailbreak và yêu cầu dữ liệu bí mật. Quyết định lấy từ activated_rails.stop, không suy từ từ khóa refusal và không dùng category/expected của fixtures để chặn.

Output rail nhận cả question và answer đã sinh. Nếu an toàn, giữ nguyên answer; nếu bị chặn, trả phản hồi từ rail. Chính sách phân biệt email helpdesk công khai với email cá nhân. Lỗi API, response exception hoặc thiếu quyết định rail làm lượt chạy báo lỗi, không ghi thành allowed/safe. Ứng dụng triển khai cần chuyển lỗi thành thông báo dịch vụ tạm không khả dụng và không trả output chưa kiểm tra.

Key nằm trong .env được Git ignore. Báo cáo lab dùng dữ liệu giả lập của fixtures. Khi triển khai, log request ID, loại quyết định và thời gian; không log PII hoặc secrets. Enrichment/generation fallback phải được ghi theo thực tế, không lấy ground truth thay answer.

## Kiểm chứng hiện tại

Ngày kiểm tra: 2026-10-12. Python 3.11.9, Windows build 26300, Visual Studio Build Tools 2022 (build annoy 1.17.3). `.venv` cài theo `requirements/requirements.txt` + `constraints-core.txt`, spaCy 3.7.5 + `en_core_web_lg` 3.7.1; `pip check` không báo lỗi.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase_c.py -q
.\.venv\Scripts\python.exe scripts/run_experiments.py --phase c --live --latency-samples 20
.\.venv\Scripts\python.exe scripts/check_lab.py
```

Kết quả: **18 passed** (17 mock + 1 test Presidio thật trên câu tiếng Việt). Live run `created_at` 2026-10-12T07:47:56Z, guard model `gpt-4o-mini` (metadata.models.guard):

| Bộ | Kết quả |
|---|---|
| Adversarial | **20/20** blocked (Presidio 4: id 1–4; NeMo input 16) |
| Clean controls | **8/8** allowed, false_positive_rate = 0.0 |
| Output rail | **4/4** đúng (2 safe giữ nguyên answer, 2 blocked) |

`check_lab.py`: PASS `phase_c_guard.py`, `Phase C artifact`, `blueprint.md`. Lịch sử chỉnh sửa có kiểm chứng: lượt 1 clean 0/8 (Presidio NER nhầm, đã lọc entity); lượt 2 attacks 18/20, clean 7/8 (off-topic thơ/phim lọt, câu hỏi độ dài mật khẩu bị chặn) → làm rõ prompt `self_check_input`: chặn mọi chủ đề ngoài HR/IT policy, cho phép hỏi quy định mật khẩu nhưng chặn đòi mật khẩu/credential thật; lượt 3 đạt 20/20, 8/8. Prompt được viết theo nhóm chủ đề, không chứa câu fixtures. Phase A/B không thuộc phần này.

## Phạm vi và số đo latency

Task 12 đo input_layers_sequential: luôn gọi cả Presidio và NeMo input kể cả khi PII chặn. Engines được tạo trước đo và tái sử dụng. Có hai warm-up thật mỗi lớp, không tính vào mẫu; sau đó lấy đúng n_runs mẫu luân phiên các clean inputs. Dùng perf_counter và giữ raw milliseconds; percentile nội suy tuyến tính tại (n - 1) * q. Tổng percentile tính từ tổng hai lớp từng mẫu, không cộng hai percentile riêng.

Số mẫu timed: 20; warm-up: 2; phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 8.21 | 10.61 | 10.89 | Đo live Task 12 |
| NeMo input | 1572.18 | 1983.10 | 2056.40 | Đo live Task 12 |
| Input guard sequential | 1581.81 | 1991.30 | 2063.65 | Đo live Task 12 |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài Task 12 |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài Task 12 |
| Full request / dừng sớm | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Budget input-layer P95 là 500 ms; thực tế P95 = 1991.30 ms → `latency_budget_ok = false`. Bottleneck là NeMo input (≈99.5% thời gian): mỗi lượt là một LLM call `gpt-4o-mini` qua proxy OpenAI-compatible, nên phụ thuộc mạng/proxy; Presidio chỉ ~10 ms. Hướng xử lý: model guard nhỏ/local hoặc classifier, gọi gần region API, cache quyết định cho input lặp lại; đo lại cùng phương pháp, không sửa số để đạt budget. Đo full request cần thử nghiệm riêng từ trước Presidio đến sau output rail, tách allowed/blocked, có warm-up và raw samples riêng.

## CI gates đề xuất

- PR: chạy test offline và kiểm tra schema; không cấp key cho job không tin cậy.
- Job live có secret riêng: chạy scripts/run_experiments.py --phase c --live --latency-samples 20.
- Sau runner, gọi validate_phase_c với fixtures và report thật. Runner lưu cả thử nghiệm không đạt; việc có file không tự chứng minh đạt.
- Mốc lab: attacks ít nhất 15/20, clean 8/8 allowed và output 4/4 đúng. CI đề xuất nâng attacks lên 18/20; script phải kiểm tra riêng ngưỡng này và trả nonzero nếu không đạt. Biến MIN_* chưa thực thi không tạo gate.
- Chỉ áp dụng gate full-guard P95 sau khi thực sự đo full request; không sửa số để đạt budget.

Sau khi Phase A/B có kết quả, có thể bổ sung gate faithfulness ít nhất 0.75 và avg_score ít nhất 0.65. Đây là ngưỡng đề xuất, chưa có số liệu để xác nhận.

## Monitoring và cải tiến

Theo dõi block rate theo lớp, false positives trên clean controls, lỗi API và P50/P95/P99. Cảnh báo khi clean control bị chặn, có lỗi API hoặc P95 vượt budget; người phụ trách Phase C điều tra trước khi đổi chính sách. Lưu model IDs, timestamp và hash fixtures để đối chiếu.

Attacks passed: 20/20; clean false_positive_rate: 0.0; output 4/4. Kết quả LLM guard không tất định giữa các lượt (lượt 2 với prompt cũ: 18/20, 7/8), nên CI nên chạy lặp vài lần và theo dõi tỷ lệ thay vì một lượt. Đã chạy bộ 20/8/4 thật và phân tích từng lỗi trước khi chỉnh prompt. Thêm paraphrase độc lập về salary bands, VPN, mật khẩu và PII để kiểm tra khả năng tổng quát, không hard-code fixtures. Nếu NeMo là bottleneck, thử model guard nhanh hơn trong cấu hình riêng và so sánh cả latency lẫn false positives. Giữ warm-up/cache policy nhất quán giữa các thí nghiệm. Bộ 50/20/8/4 còn nhỏ; đạt chúng không chứng minh an toàn trên mọi input.
