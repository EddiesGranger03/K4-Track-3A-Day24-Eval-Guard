# Nhóm thực hiện K4 Track 3A

Tên nhóm: SKUNN

Repo chung: {{Link repo}}

Trưởng nhóm/người nộp: {{Họ tên và MSSV}}

Ngày lab/deadline áp dụng: {{Ngày giờ theo thông báo lớp}} — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: {{Commit SHA}}

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Nguyễn Nam Khánh | 2A202602568 | CP0 + Phase A: tích hợp m1–m5, sinh 50 answers, T1–T4 và phân tích lỗi | Nhánh `NguyenNamKhanh-2A202602568`; `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, `doc/reports/failure_clusters.md` |
| 2 | Nguyễn Khánh Sơn | 2A202602388 | Phase B: pairwise judge + swap/kappa/bias (`src/phase_b_judge.py` T5–T8) + `doc/reports/bias_report.md` | Branch `Son` commit 176b16f; `artifacts/judge_results.json` (κ=1.0); checker PASS Phase B |
| 3 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 4 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |

Người tích hợp/chạy batch/nộp link: {{Họ tên, công việc và bằng chứng}}.

## Môi trường và chuẩn bị trước lớp

OS/Python: macOS 27.0.1 arm64, Python 3.11.16 trong `.venv`. Dependencies và model revisions được ghi tại `artifacts/cp0_environment.json`.
Virtualenv/dependencies/imports: `python -m pip check` không có xung đột; import ragas, nemoguardrails, presidio_analyzer và spacy thành công. `en_core_web_lg` đã cài. Đây là bằng chứng imports, chưa chứng minh runtime guardrails Phase C.
Models/Qdrant/50 answers: Qdrant `v1.9.7`, BGE-M3 và BGE reranker-v2-m3; dense search thực tế dùng Qdrant server. 26 documents/109 chunks, 50 answers LLM với distribution 20/20/10, không extractive fallback. Hai PDF scan chưa OCR vẫn giữ trong corpus. Enrichment dùng cache các request API thành công. Xem `artifacts/run_logs/cp0_setup.log` và báo cáo giới hạn.
Nếu cài full NeMo chưa thành công, ghi lỗi thực tế; không dùng unit test pass
hoặc pip resolve để khẳng định runtime đã chạy.

## INDIVIDUAL

### NguyenNamKhanh-2A202602568

- Phần được giao và thực tế hoàn tất: CP0 và Phase A. Tích hợp m1–m5 từ repo Day 18; sửa dense search tương thích qdrant-client 1.9.2; điều chỉnh enrichment dùng cấu hình OpenAI. Implement `group_by_distribution`, `run_ragas_50q`, `bottom_10`, `cluster_analysis` trong `src/phase_a_ragas.py`; adapter m4 trả kết quả theo đúng thứ tự và model IDs thật, cache số đo hợp lệ, retry lỗi và từ chối điểm thiếu/NaN.
- Bằng chứng: nhánh `NguyenNamKhanh-2A202602568`, commit `Complete CP0 and Phase A with live RAGAS evidence`; `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, `artifacts/cp0_environment.json`, logs trong `artifacts/run_logs/`, `doc/reports/failure_clusters.md`. Commit dùng để chấm của repo chung cần được nhóm ghi sau khi tích hợp/review.
- Cách kiểm tra: setup và `python scripts/run_experiments.py --phase a --live` đã chạy thật, 50 câu × 4 metrics hữu hạn. Regression Phase A/support/report contracts/Qdrant compatibility: 75 tests pass. Unit tests chỉ kiểm tra giao diện/tính toán; bằng chứng API nằm trong log live.
- Các khái niệm cần giải thích khi trình bày: giữ answer và ground_truth tách biệt; evaluator metadata từ m4; worst_metric là tín hiệu cần kiểm chứng; nhóm yếu được chọn theo mean thay vì số câu. Báo cáo đối chiếu Q9/Q24 (generation) với Q21/Q33 (thiếu nguồn multi-hop), Q39/Q50 (phiên bản/phủ định).
- Giới hạn: chưa OCR hai PDF scan; 8 câu LLM trả “Không tìm thấy.”; chưa thực hiện ablation hoặc sửa generation để cải thiện điểm. Phase B/C và full NeMo runtime không thuộc phần đã chạy này. Không sửa ground truth, không bỏ policy cũ và không thay số đo lỗi bằng 0.
- Nguồn/AI hỗ trợ: pipeline từ repo `K4-Track3A-DAY18-NguyenNamKhanh-2A202602568-ProductionRAG`; Codex hỗ trợ triển khai, debug, chạy kiểm chứng và viết phân tích từ artifacts thật. Nguyễn Nam Khánh cần review và hiểu phần được hỗ trợ trước khi trình bày/nộp.

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### NguyenKhanhSon-2A202602388

- Phần được giao và phần thực tế đã làm: Phase B sau khi đổi task với Nguyễn Nam Khánh — implement T5 `pairwise_judge`, T6 `swap_and_average`, T7 `cohen_kappa`, T8 `bias_report` trong `src/phase_b_judge.py`; chạy live ra `artifacts/judge_results.json`; điền `doc/reports/bias_report.md`.
- Bằng chứng: branch `Son` commit 176b16f (`phase_b_judge.py`, `judge_results.json`, `bias_report.md`, `doc/indi.md`); κ=1.0 trên 10 nhãn, pair_sources đúng quy định.
- Cách kiểm tra: `pytest tests/test_phase_b.py -q` 8/8 passed; `run_experiments.py --phase b --live` lưu artifact; `check_lab.py` PASS cả 3 mục Phase B.
- Điều đã học: swap-and-average phát hiện position bias; phân biệt winner A/B/tie với nhãn 0/1; κ hiệu chỉnh đồng thuận ngẫu nhiên; verbosity bias bị nhiễu khi đáp án dài cũng đầy đủ ý hơn.
- Giới hạn/cách xử lý: mẫu nhỏ (5 cặp/10 nhãn) nên bias chỉ là dấu hiệu; 50 answers là `extractive_fallback` (ngoài scope, đã cảnh báo nhóm); fix thiếu `jsonschema` và `OPENAI_BASE_URL` cho runner.
- Nguồn/AI hỗ trợ nếu có: AI assistant implement theo hợp đồng tests, tự kiểm chứng bằng mock tests + live run + checker.

### {{HoVaTen}}-{{MSSV}}

- Phần được giao và phần thực tế đã làm: {{Nhiệm vụ, file/hàm, mục đích}}.
- Bằng chứng: {{Commit/PR và artifacts/reports liên quan}}.
- Cách kiểm tra: {{Unit mock hoặc live experiment, lệnh và kết quả}}.
- Điều đã học: {{Khái niệm và cách thể hiện trong bài}}.
- Giới hạn/cách xử lý: {{Vấn đề và kiểm chứng}}.
- Nguồn/AI hỗ trợ nếu có: {{Công cụ, phạm vi, cách tự kiểm chứng}}.

## Cập nhật sau khi nộp

{{Ghi phiên bản nộp; nếu sửa sau deadline, ghi commit/thời điểm/lý do và thông báo
coach cho phép áp dụng bản cập nhật. Nếu không có cập nhật, ghi rõ không có.}}
