# Nhóm thực hiện K4 Track 3A

Tên nhóm: {{Tên nhóm}}

Repo chung: {{Link repo}}

Trưởng nhóm/người nộp: {{Họ tên và MSSV}}

Ngày lab/deadline áp dụng: {{Ngày giờ theo thông báo lớp}} — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: {{Commit SHA}}

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 2 | Ngô Đinh Minh Nhật | 2A202602569 | Phase C: `src/phase_c_guard.py` T9a–T12 + `guardrails/config.yml` + `doc/reports/blueprint.md` | Branch `ndmnhat`; `artifacts/guard_results.json` (attacks 20/20, clean 8/8, output 4/4); checker PASS Phase C |
| 3 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |

Người tích hợp/chạy batch/nộp link: {{Họ tên, công việc và bằng chứng}}.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler (máy Ngô Đinh Minh Nhật): Windows build 26300, Python 3.11.9,
Visual Studio Build Tools 2022. Lượt cài đầu dừng ở Annoy 1.17.3 do thiếu MSVC;
sau khi cài Build Tools, `pip install annoy==1.17.3` build thành công.

Virtualenv/dependencies/imports: `.venv` (Python 3.11) cài
`requirements/requirements.txt -c requirements/constraints-core.txt`; `pip check`
"No broken requirements found". spaCy 3.7.5 + `en_core_web_lg` 3.7.1 (tải từ
HuggingFace vì GitHub release quá chậm; spaCy 3.7.5 vẫn trong `>=3.7,<3.9`).
Imports `nemoguardrails`, `presidio_analyzer`, `spacy.load('en_core_web_lg')` OK;
Phase C chạy live thành công (xem blueprint).

Models/Qdrant/50 answers: chưa sinh `artifacts/answers_50q.json` trên máy này;
Phase A/B do thành viên khác phụ trách.

Hỗ trợ AI: Codex và Claude Code hỗ trợ triển khai T9a–T12, debug môi trường và
chỉnh guard; kiểm chứng bằng unit tests, live run và `check_lab.py`.
Xem [blueprint](reports/blueprint.md).

## INDIVIDUAL

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### NgoDinhMinhNhat-2A202602569

- Phần được giao và phần thực tế đã làm: Phase C (35đ) trong `src/phase_c_guard.py` — T9a `pii_scan` (Presidio + recognizer VN_CCCD/VN_PHONE, chỉ giữ entity có định dạng), T9b `check_input_rail` và T11 `check_output_rail` (đọc quyết định từ `activated_rails.stop`, lỗi runtime NeMo raise chứ không ghi thành allowed/safe), T10 `run_adversarial_suite` (Presidio → NeMo input, một `asyncio.run`), T12 `measure_p95_latency` (2 warm-up, 20 mẫu, luôn đo cả hai lớp). Chỉnh prompt `self_check_input` trong `guardrails/config.yml`; điền `doc/reports/blueprint.md`.
- Bằng chứng: branch `ndmnhat`; `artifacts/guard_results.json` (live 2026-10-12T07:47:56Z, guard `gpt-4o-mini`): attacks 20/20, clean 8/8 (FPR 0.0), output 4/4; input guard P95 1991.30 ms.
- Cách kiểm tra: `pytest tests/test_phase_c.py -q` → 18 passed; `python scripts/run_experiments.py --phase c --live --latency-samples 20` → "Adversarial suite: 28/28 passed"; `check_lab.py` PASS `phase_c_guard.py`, `Phase C artifact`, `blueprint.md`.
- Điều đã học: guard nhiều lớp — Presidio rẻ (~10 ms) cho PII có định dạng, LLM self-check cho ý định (jailbreak, off-topic, impersonation); NER tiếng Anh trên văn bản tiếng Việt gây false positive hàng loạt nên phải giới hạn entity; đọc quyết định rail thay vì đoán từ chuỗi refusal; P95 tính từ raw samples với nội suy tuyến tính, tổng tính theo từng mẫu.
- Giới hạn/cách xử lý: lượt 1 clean 0/8 (Presidio NER) → lọc entity + test Presidio thật; lượt 2 attacks 18/20, clean 7/8 → làm rõ prompt theo nhóm chủ đề (không chép fixtures); LLM guard không tất định nên kết quả có thể dao động giữa các lượt. P95 vượt budget 500 ms do NeMo LLM call qua proxy — ghi số thật, chưa tối ưu.
- Nguồn/AI hỗ trợ nếu có: Codex và Claude Code hỗ trợ code, debug môi trường (Annoy/MSVC, spaCy model) và phân tích lỗi; tự kiểm chứng bằng unit tests, 3 lượt live và checker.

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
