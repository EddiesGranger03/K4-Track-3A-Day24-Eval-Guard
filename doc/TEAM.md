# Nhóm thực hiện K4 Track 3A

Tên nhóm: SKUNN

Repo chung: https://github.com/EddiesGranger03/K4-Track-3A-Day24-Eval-Guard

Trưởng nhóm/người nộp: Nguyễn Phi Nhật — 2A202602658

Ngày lab/deadline áp dụng: 12/10/2026 23:59 — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: 5eac362c3e414c3e8ad6f54dd00d3d4ec74a9582

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Nguyễn Nam Khánh | 2A202602568 | CP0 + Phase A: tích hợp m1–m5, sinh 50 answers, T1–T4 và phân tích lỗi | Nhánh `NguyenNamKhanh-2A202602568`; `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, `doc/reports/failure_clusters.md` |
| 2 | Nguyễn Khánh Sơn | 2A202602388 | Phase B: pairwise judge + swap/kappa/bias (`src/phase_b_judge.py` T5–T8) + `doc/reports/bias_report.md` | Branch `Son` commit 176b16f; `artifacts/judge_results.json` (κ=1.0); checker PASS Phase B |
| 3 | Ngô Đinh Minh Nhật | 2A202602569 | Phase C: `src/phase_c_guard.py` T9a–T12 + `guardrails/config.yml` + `doc/reports/blueprint.md` | Branch `ndmnhat`; `artifacts/guard_results.json` (attacks 20/20, clean 8/8, output 4/4); checker PASS Phase C |
| 4 | Nguyễn Phi Nhật | 2A202602658 | Task 13 Blueprint CI/CD, tích hợp code, kiểm thử hệ thống & nộp bài | Nhánh `NgPhiNhat`; `doc/reports/blueprint.md`, `doc/TEAM.md`, `.gitattributes`, `artifacts/judge_results.json` |

Người tích hợp/chạy batch/nộp link: Nguyễn Phi Nhật — 2A202602658, tích hợp code các nhánh, chuẩn hóa LF, chạy live đối soát Phase B, chạy check_lab và nộp bài.

## Môi trường và chuẩn bị trước lớp

OS/Python Phase A/B: macOS 27.0.1 arm64, Python 3.11.16 trong `.venv`. Dependencies và model revisions được ghi tại `artifacts/cp0_environment.json`.

OS/Python/compiler Phase C (máy Ngô Đinh Minh Nhật): Windows build 26300, Python 3.11.9,
Visual Studio Build Tools 2022. Lượt cài đầu dừng ở Annoy 1.17.3 do thiếu MSVC;
sau khi cài Build Tools, `pip install annoy==1.17.3` build thành công.

Virtualenv/dependencies/imports: Phase A/B `python -m pip check` không có xung đột; import ragas, nemoguardrails, presidio_analyzer và spacy thành công. `en_core_web_lg` đã cài. Phase C `.venv` (Python 3.11) cài
`requirements/requirements.txt -c requirements/constraints-core.txt`; `pip check`
"No broken requirements found". spaCy 3.7.5 + `en_core_web_lg` 3.7.1 (tải từ
HuggingFace vì GitHub release quá chậm; spaCy 3.7.5 vẫn trong `>=3.7,<3.9`).
Imports `nemoguardrails`, `presidio_analyzer`, `spacy.load('en_core_web_lg')` OK;
Phase C chạy live thành công (xem blueprint).

Models/Qdrant/50 answers: Qdrant `v1.9.7`, BGE-M3 và BGE reranker-v2-m3; dense search thực tế dùng Qdrant server. 26 documents/109 chunks, 50 answers LLM với distribution 20/20/10, không extractive fallback. Hai PDF scan chưa OCR vẫn giữ trong corpus. Enrichment dùng cache các request API thành công. Xem `artifacts/run_logs/cp0_setup.log` và báo cáo giới hạn. Phase C dùng `artifacts/guard_results.json` và `doc/reports/blueprint.md`.

Xem [blueprint](reports/blueprint.md).

## INDIVIDUAL

### NguyenNamKhanh-2A202602568

- Phần được giao và thực tế hoàn tất: CP0 và Phase A. Tích hợp m1–m5 từ repo Day 18; sửa dense search tương thích qdrant-client 1.9.2; điều chỉnh enrichment dùng cấu hình OpenAI. Implement `group_by_distribution`, `run_ragas_50q`, `bottom_10`, `cluster_analysis` trong `src/phase_a_ragas.py`; adapter m4 trả kết quả theo đúng thứ tự và model IDs thật, cache số đo hợp lệ, retry lỗi và từ chối điểm thiếu/NaN.
- Bằng chứng: nhánh `NguyenNamKhanh-2A202602568`, commit `Complete CP0 and Phase A with live RAGAS evidence`; `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, `artifacts/cp0_environment.json`, logs trong `artifacts/run_logs/`, `doc/reports/failure_clusters.md`. Commit dùng để chấm của repo chung cần được nhóm ghi sau khi tích hợp/review.
- Cách kiểm tra: setup và `python scripts/run_experiments.py --phase a --live` đã chạy thật, 50 câu × 4 metrics hữu hạn. Regression Phase A/support/report contracts/Qdrant compatibility: 75 tests pass. Unit tests chỉ kiểm tra giao diện/tính toán; bằng chứng API nằm trong log live.
- Các khái niệm cần giải thích khi trình bày: giữ answer và ground_truth tách biệt; evaluator metadata từ m4; worst_metric là tín hiệu cần kiểm chứng; nhóm yếu được chọn theo mean thay vì số câu. Báo cáo đối chiếu Q9/Q24 (generation) với Q21/Q33 (thiếu nguồn multi-hop), Q39/Q50 (phiên bản/phủ định).
- Giới hạn: chưa OCR hai PDF scan; 8 câu LLM trả “Không tìm thấy.”; chưa thực hiện ablation hoặc sửa generation để cải thiện điểm. Phase B/C và full NeMo runtime không thuộc phần đã chạy này. Không sửa ground truth, không bỏ policy cũ và không thay số đo lỗi bằng 0.
- Nguồn/AI hỗ trợ: pipeline từ repo `K4-Track3A-DAY18-NguyenNamKhanh-2A202602568-ProductionRAG`; Codex hỗ trợ triển khai, debug, chạy kiểm chứng và viết phân tích từ artifacts thật. Nguyễn Nam Khánh cần review và hiểu phần được hỗ trợ trước khi trình bày/nộp.

### NguyenKhanhSon-2A202602388

- Phần được giao và phần thực tế đã làm: Phase B sau khi đổi task với Nguyễn Nam Khánh — implement T5 `pairwise_judge`, T6 `swap_and_average`, T7 `cohen_kappa`, T8 `bias_report` trong `src/phase_b_judge.py`; chạy live ra `artifacts/judge_results.json`; điền `doc/reports/bias_report.md`.
- Bằng chứng: branch `Son` commit 176b16f (`phase_b_judge.py`, `judge_results.json`, `bias_report.md`, `doc/indi.md`); κ=1.0 trên 10 nhãn, pair_sources đúng quy định.
- Cách kiểm tra: `pytest tests/test_phase_b.py -q` 8/8 passed; `run_experiments.py --phase b --live` lưu artifact; `check_lab.py` PASS cả 3 mục Phase B.
- Điều đã học: swap-and-average phát hiện position bias; phân biệt winner A/B/tie với nhãn 0/1; κ hiệu chỉnh đồng thuận ngẫu nhiên; verbosity bias bị nhiễu khi đáp án dài cũng đầy đủ ý hơn.
- Giới hạn/cách xử lý: mẫu nhỏ (5 cặp/10 nhãn) nên bias chỉ là dấu hiệu; 50 answers là `extractive_fallback` (ngoài scope, đã cảnh báo nhóm); fix thiếu `jsonschema` và `OPENAI_BASE_URL` cho runner.
- Nguồn/AI hỗ trợ nếu có: AI assistant implement theo hợp đồng tests, tự kiểm chứng bằng mock tests + live run + checker.

### NgoDinhMinhNhat-2A202602569

- Phần được giao và phần thực tế đã làm: Phase C (35đ) trong `src/phase_c_guard.py` — T9a `pii_scan` (Presidio + recognizer VN_CCCD/VN_PHONE, chỉ giữ entity có định dạng), T9b `check_input_rail` và T11 `check_output_rail` (đọc quyết định từ `activated_rails.stop`, lỗi runtime NeMo raise chứ không ghi thành allowed/safe), T10 `run_adversarial_suite` (Presidio → NeMo input, một `asyncio.run`), T12 `measure_p95_latency` (2 warm-up, 20 mẫu, luôn đo cả hai lớp). Chỉnh prompt `self_check_input` trong `guardrails/config.yml`; điền `doc/reports/blueprint.md`.
- Bằng chứng: branch `ndmnhat`; `artifacts/guard_results.json` (live 2026-10-12T07:47:56Z, guard `gpt-4o-mini`): attacks 20/20, clean 8/8 (FPR 0.0), output 4/4; input guard P95 1991.30 ms.
- Cách kiểm tra: `pytest tests/test_phase_c.py -q` → 18 passed; `python scripts/run_experiments.py --phase c --live --latency-samples 20` → "Adversarial suite: 28/28 passed"; `check_lab.py` PASS `phase_c_guard.py`, `Phase C artifact`, `blueprint.md`.
- Điều đã học: guard nhiều lớp — Presidio rẻ (~10 ms) cho PII có định dạng, LLM self-check cho ý định (jailbreak, off-topic, impersonation); NER tiếng Anh trên văn bản tiếng Việt gây false positive hàng loạt nên phải giới hạn entity; đọc quyết định rail thay vì đoán từ chuỗi refusal; P95 tính từ raw samples với nội suy tuyến tính, tổng tính theo từng mẫu.
- Giới hạn/cách xử lý: lượt 1 clean 0/8 (Presidio NER) → lọc entity + test Presidio thật; lượt 2 attacks 18/20, clean 7/8 → làm rõ prompt theo nhóm chủ đề (không chép fixtures); LLM guard không tất định nên kết quả có thể dao động giữa các lượt. P95 vượt budget 500 ms do NeMo LLM call qua proxy — ghi số thật, chưa tối ưu.
- Nguồn/AI hỗ trợ nếu có: Codex, Claude Code (hỗ trợ code/debug); tự kiểm chứng bằng tests, live run và checker.

### NguyenPhiNhat-2A202602658

- Phần được giao và thực tế hoàn tất: Task 13 (Blueprint CI/CD) trong `doc/reports/blueprint.md`; tích hợp toàn bộ code của 3 nhánh (`NguyenNamKhanh-2A202602568`, `Son`, `ndmnhat`) vào nhánh `NgPhiNhat`; chuẩn hóa line-ending LF bằng `.gitattributes` để khắc phục lỗi lệch hash trên Windows; chạy thực nghiệm live đối soát lại Phase B khi phát hiện `judge_results.json` cũ dùng extractive answers lệch với answers sinh bằng LLM của Phase A (đưa Cohen's κ lên 1.0 và position bias về 0.0); hoàn thiện kiểm tra toàn diện bằng `scripts/check_lab.py` và chuẩn bị nộp bài.
- Bằng chứng: Nhánh `NgPhiNhat`; `doc/reports/blueprint.md`, `doc/TEAM.md`, `.gitattributes`, `artifacts/judge_results.json` cập nhật theo live run; kết quả `check_lab.py` PASS toàn bộ các hạng mục.
- Cách kiểm tra: Chạy `py -3.14 scripts/check_lab.py` (tất cả các mục PASS 100%); chạy `pytest tests/test_phase_a.py -q` (14 passed), `pytest tests/test_phase_b.py -q` (8 passed), `pytest tests/test_phase_c.py -q` (17 passed); đối chiếu schema và source hashes của 4 artifact JSON.
- Điều đã học: Quy trình thiết kế CI/CD Guardrails đa tầng (RAG Quality Gate, Judge Reliability Gate, Guardrail Gate); kỹ thuật swap-and-average để khử triệt để position bias của LLM Judge; tầm quan trọng của việc chuẩn hóa end-of-line (LF) giữa các môi trường Windows và macOS/Linux để đảm bảo tính toàn vẹn của mã băm SHA256; nguyên lý Presidio PII regex kết hợp NeMo self-check để đạt 100% block rate mà vẫn giữ 0% false positive.
- Giới hạn/cách xử lý: P95 latency của NeMo input guard thực tế đạt 1991.30 ms (vượt budget 500 ms) do gọi LLM `gpt-4o-mini` qua cloud API; nhóm ghi nhận số liệu đo thực tế trung thực và đề xuất phương án tối ưu trong blueprint (dùng SLM local, classifier hoặc caching) thay vì sửa số liệu.
- Nguồn/AI hỗ trợ nếu có: Antigravity IDE, OpenAI API; tự kiểm chứng toàn bộ bằng unit test offline, runner live và checker tự động.

## Cập nhật sau khi nộp

Bản nộp chính thức trước deadline 23:59 ngày 12/10/2026. Không có cập nhật sau deadline.

