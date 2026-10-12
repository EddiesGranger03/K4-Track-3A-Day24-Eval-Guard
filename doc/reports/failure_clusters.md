# Phân tích lỗi Phase A — CP0/CP1

Người phụ trách: Nguyễn Nam Khánh — 2A202602568 (MSSV theo repo Day 18).
Phạm vi: phần CP0 và T1–T4 của repo nhóm; các phase B/C do thành viên phụ trách riêng.

Nguồn số đo: `artifacts/ragas_50q.json`. Thời điểm xuất báo cáo: 2026-10-12T12:20:05.494604+07:00 (UTC+07:00).
Các hash đầu vào trong metadata đối chiếu `answers_50q.json` và `test_set_50q.json`; không dùng ground truth để sinh answers.

## Môi trường và luồng thực nghiệm

macOS 27.0.1, Python 3.11.16, virtualenv `.venv`. `pip check` không có xung đột. RAGAS 0.1.22, LangChain 0.2.17, langchain-core 0.2.43, langchain-openai 0.1.25, OpenAI SDK 1.109.1, NumPy 1.26.4, PyArrow 19.0.1, qdrant-client 1.9.2. Chi tiết phiên bản, corpus hash và model revisions: `artifacts/cp0_environment.json`.

Qdrant server dùng image `qdrant/qdrant:v1.9.7`, collection `lab24_production`. 109 child chunks của 26 tài liệu đọc được đi qua enrichment, BM25 + BGE-M3 dense search, RRF và BGE reranker-v2-m3 top 3. Bản m2 Day 18 dùng `query_points` không tồn tại trong client 1.9.2 đã được sửa sang `search`; log CP0 lần chạy hiện tại xác nhận dense search trên `qdrant_server`. Bản answers trước sửa chỉ có BM25 đã được thay bằng lần sinh lại qua hybrid retrieval.

Hai PDF scan `BCTC.pdf` và `Nghi_dinh_so_13-2023_ve_bao_ve_du_lieu_ca_nhan_508ee.pdf` chưa có text layer và chưa OCR. Các file vẫn giữ nguyên trong corpus. Chưa được phép kết luận hệ thống trả lời đủ nội dung hai tài liệu này; không quy mọi lỗi trong 50 câu cho việc thiếu PDF khi chưa có bằng chứng.

Generation models: gpt-4o-mini-2024-07-18. Evaluator models thực sự được cấu hình và gọi: gpt-4o-mini, text-embedding-3-small. Vai trò judge/guard không chạy trong Phase A và được ghi là list rỗng.

Cả 50 records có `generation_mode=llm`, không có extractive fallback. 8 answers là câu “Không tìm thấy.” do LLM tạo (ids 9, 21, 22, 24, 33, 39, 40, 50); đây là lỗi/giới hạn của câu trả lời, không phải fallback của setup. Enrichment dùng cache của các request OpenAI thành công trước đó, không gọi lại 109 chunks. RAGAS đo thật 4 metrics; lỗi/missing/NaN bị từ chối và không thay bằng số giả. Các rows đo thành công được cache theo hash của inputs + evaluator models để phục hồi khi interrupted.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---:|---:|---:|
| faithfulness | 0.883333 | 0.425000 | 0.866667 |
| answer_relevancy | 0.497774 | 0.392090 | 0.509034 |
| context_precision | 0.958333 | 0.929167 | 0.966667 |
| context_recall | 0.900000 | 0.854167 | 0.650000 |
| avg_score | 0.809860 | 0.650106 | 0.748092 |

Bảng dùng mean của từng nhóm, không lấy nhóm có nhiều câu nhất làm nhóm yếu. Avg_score mỗi câu là trung bình bốn metric với trọng số bằng nhau. Điểm phản ánh đánh giá của evaluator trong lượt này, không phải human accuracy.

## Bottom 10 từ Task 3

| Rank | ID | Distribution | Question | Avg score | Worst metric | Diagnosis | Suggested fix |
|---:|---:|---|---|---:|---|---|---|
| 1 | 39 | multi_hop | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | 0.250000 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 2 | 40 | multi_hop | Nhân viên cấp Manager có thời hạn thử việc 90 ngày, đang trong tháng thứ 3, phát hiện vi phạm bảo mật. Họ nên và không nên làm gì theo chính sách? | 0.333333 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 3 | 50 | adversarial | Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không? | 0.333333 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 4 | 21 | multi_hop | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | 0.375000 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 5 | 33 | multi_hop | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | 0.375000 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 6 | 9 | factual | Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con? | 0.500000 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 7 | 22 | multi_hop | Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT? | 0.500000 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 8 | 24 | multi_hop | Nhân viên tạm ứng 15 triệu, sau 20 ngày mới thanh toán. Bị phạt bao nhiêu? | 0.500000 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 9 | 31 | multi_hop | Nhân viên đi công tác trong nước, ở khách sạn 2 đêm với giá 1.500.000 VNĐ/đêm. Công ty thanh toán tối đa bao nhiêu cho tiền khách sạn? | 0.542130 | faithfulness | Có thể có claim chưa được contexts hỗ trợ; cần đối chiếu từng claim | Ràng buộc generation theo nguồn và gắn citation cho từng claim |
| 10 | 7 | factual | Nghỉ phép không lương 20 ngày cần ai phê duyệt? | 0.576831 | answer_relevancy | Câu trả lời có thể chưa bao phủ đúng trọng tâm câu hỏi | Tách các ý cần trả lời trong prompt và kiểm tra phủ định/điều kiện |

Các diagnosis/fix trong bảng lấy nguyên văn từ Task 3 và JSON. Diagnosis theo worst_metric là giả thuyết ban đầu; cần đối chiếu nội dung để định vị retrieval/generation. Sắp xếp ổn định theo avg_score tăng dần; khi bằng điểm giữ thứ tự đầu vào.

## Đối chiếu nội dung để phân biệt nguyên nhân

**Q9 — generation bỏ sót bằng chứng có sẵn** (faithfulness=0.0000, answer_relevancy=0.0000, context_precision=1.0000, context_recall=1.0000). Answer là “Không tìm thấy.” nhưng context 1 có “Sinh con (nam giới): 5 ngày làm việc liên tục” và context 2 nêu nghỉ phép đặc biệt không trừ phép năm. Reference yêu cầu đúng 5 ngày và điều kiện không trừ phép năm. Không nên kết luận retrieval hoàn toàn thất bại; cần sửa generation để đọc đủ các dòng liên quan trong context.

**Q24 — generation thiếu suy luận số học** (faithfulness=0.0000, answer_relevancy=0.0000, context_precision=1.0000, context_recall=1.0000). Cả ba contexts cung cấp thời hạn 15 ngày, phí 2%/tháng và công thức pro-rata 30 ngày. Question cho 15 triệu và thanh toán sau 20 ngày, reference tính 2% × 15.000.000 × (5/30) = 50.000 VNĐ. Answer vẫn là “Không tìm thấy.”. Dữ kiện đủ cho phép tính; lỗi này thiên về generation thay vì thiếu retrieval.

**Q21/Q33 — retrieval thiếu nguồn cho multi-hop** (Q21: faithfulness=0.0000, answer_relevancy=0.0000, context_precision=1.0000, context_recall=0.5000; Q33: faithfulness=0.0000, answer_relevancy=0.0000, context_precision=1.0000, context_recall=0.5000). Q21 hỏi cả phép năm và lương Senior nhưng cả ba contexts tập trung vào phép năm, có cả v2023/v2024, không có mức lương. Q33 hỏi phụ cấp và phép năm Manager 12 năm; contexts có phép năm và bảng lương nhưng thiếu phụ cấp ăn trưa/điện thoại. Rerank top 3 chưa bảo đảm bao phủ từng ý hỏi. Generation từ chối toàn bộ còn bỏ mất phần có thể trả lời.

**Q22 — thiếu ngưỡng phê duyệt** (faithfulness=0.0000, answer_relevancy=0.0000, context_precision=1.0000, context_recall=1.0000). Contexts có xác nhận cấu hình CNTT và yêu cầu 3 báo giá trên 10 triệu, nhưng thiếu bảng phân quyền phê duyệt mua sắm; context 3 nhắc mức 30 triệu của đào tạo là nguồn gây nhiễu. Reference yêu cầu Director phê duyệt laptop 30 triệu. Không được suy thẩm quyền mua sắm từ chính sách đào tạo chỉ vì trùng số tiền.

**Q39 — version comparison thiếu điều khoản** (faithfulness=0.0000, answer_relevancy=0.0000, context_precision=0.0000, context_recall=1.0000). Contexts giữ cả phiên bản mật khẩu 1.0/2.0 và nêu 8/12 ký tự, nhưng không bao phủ đầy đủ chu kỳ 90/120 ngày và MFA. Answer không tìm thấy dù đã có một phần dữ kiện. Cần lấy section/parent đầy đủ của cả hai phiên bản, và prompt trả lời từng ý có bằng chứng thay vì từ chối toàn bộ.

**Q50 — phủ định và fragment boundary** (faithfulness=0.0000, answer_relevancy=0.0000, context_precision=1.0000, context_recall=0.3333). Context 1 chứa “Không sử dụng VPN cá nhân (NordVPN, ExpressVPN) trong”, trong khi context 2 bắt đầu lại từ “VPN cá nhân ... trong mạng công ty” nên mất từ phủ định ở đầu fragment. Answer không tìm thấy; reference yêu cầu phủ định việc dùng VPN cá nhân và dùng WireGuard công ty. Cần giữ nguyên list item/parent khi cắt chunks và đọc phủ định; chức danh Manager trong câu hỏi không tạo ngoại lệ chính sách.

**Đối chứng Q49/Q46** (Q49: faithfulness=0.6667, answer_relevancy=0.4507, context_precision=1.0000, context_recall=0.6667; Q46: faithfulness=1.0000, answer_relevancy=0.4605, context_precision=1.0000, context_recall=0.6667). Q49 có cả policy nghỉ phép v2023/v2024 trong contexts; answer phân biệt đúng 12 ngày cũ và 15 ngày hiện hành. Q46 trả lời đúng “KHÔNG được nghỉ phép năm” theo context thử việc. Những trường hợp đúng này không chứng minh mọi câu version conflict/negation đều được xử lý; Q39/Q50 cho thấy giới hạn còn tồn tại.

## Matrix và nhóm yếu nhất

| Worst metric | factual | multi_hop | adversarial | Tổng |
|---|---:|---:|---:|---:|
| faithfulness | 3 | 12 | 1 | 16 |
| answer_relevancy | 13 | 8 | 6 | 27 |
| context_precision | 1 | 0 | 0 | 1 |
| context_recall | 3 | 0 | 3 | 6 |

Nhóm có mean thấp nhất: **multi_hop = 0.650106**. Worst metric xuất hiện nhiều nhất: **answer_relevancy**, 27/50 câu.
Nhóm multi_hop có mean thấp nhất (0.6501). answer_relevancy là worst_metric của 27/50 câu. Tách các ý cần trả lời trong prompt và kiểm tra phủ định/điều kiện. Matrix đếm mọi câu, không đồng nghĩa tất cả đều lỗi.

Matrix đếm worst_metric của tất cả 50 câu, kể cả câu có điểm cao; tổng các cột 20/20/10 chỉ là số mẫu. Nếu metric bằng điểm, ưu tiên theo thứ tự faithfulness, answer_relevancy, context_precision, context_recall. Một worst_metric thấp nhất tương đối chưa đủ khẳng định hallucination hoặc failure thật; các ví dụ nội dung ở trên giúp kiểm chứng.

## Bẫy adversarial, bonus và giới hạn

Adversarial mean 0.748092; factual mean 0.809860. Đạt điều kiện số học adversarial < factual của bonus Phase A (+4 theo rubric); việc chấm cuối do coach quyết định.
Bẫy version conflict là ids 41–45/49 (v2023-v2024 và mật khẩu v1-v2); bẫy negation/policy contradiction là ids 46–48/50. Q49 xử lý đúng khác biệt chính sách và Q46 giữ phủ định, trong khi Q50 không trả lời. Điểm adversarial thấp hơn factual, nếu có, chỉ cho thấy nhóm khó hơn theo evaluator; không tự chứng minh pipeline nhận biết bẫy.

50 câu và một lượt evaluation không đủ suy rộng production. Metric LLM có biến thiên dù temperature=0; evaluator LLM cùng họ với generation nên có thể có tương quan sai sót. Alias gpt-4o-mini là ID cấu hình evaluator, không xác nhận snapshot nhà cung cấp; generation snapshot được API trả về đã ghi trong JSON. RAGAS prompts và câu hỏi tổng hợp có thể dùng tiếng Anh trong khi corpus tiếng Việt; answer_relevancy dựa embedding nên cần đối chiếu thủ công. Reference có thể nêu nhiều chi tiết hơn question; context_recall thấp không luôn tương đương answer sai hoàn toàn. Chưa OCR hai PDF scan và chưa đo hiệu năng ngoài tập 50 câu.

## Cải tiến đề xuất và cách kiểm chứng

1. Truy vấn riêng từng ý trong câu multi-hop, fuse kết quả rồi giữ đa dạng nguồn; thử parent/section expansion để tránh top 3 toàn các chunks cùng policy. Đo lại context_recall của Q21/Q22/Q33/Q39/Q40 và so mức độ nhiễu context_precision.
2. Giữ metadata phiên bản/hiệu lực và span phủ định qua chunking. Khi câu hỏi yêu cầu so sánh cũ-mới phải giữ cả hai; khi hỏi hiện hành phải ưu tiên bản có hiệu lực, không xóa policy cũ để làm phép thử dễ hơn. Kiểm tra ids 41–50.
3. Generation liệt kê từng ý, trả lời phần có context và chỉ nêu thiếu dữ kiện cho phần chưa có; cho phép tính toán khi công thức và dữ kiện đều có, gắn nguồn cho từng claim. Kiểm tra Q9/Q24, đồng thời không tăng unsupported claims.
4. OCR hai PDF scan, kiểm tra chất lượng text và giữ provenance trang/tài liệu trước khi đưa vào index. Đây là kế hoạch, chưa thực hiện trong lượt hiện tại.
5. Mỗi cải tiến cần chạy trên cùng bộ 50 câu, so score từng id và bổ sung tập holdout để tránh overfit. Không chỉ tăng mean mà bỏ qua nhóm adversarial hoặc độ đầy đủ multi-hop. Các cải tiến ở mục này chưa được đo sau thay đổi.

## Bằng chứng và bàn giao cho team

Kiểm tra toàn bộ phạm vi CP0/Phase A offline bằng `python scripts/validate_phase_a_submission.py` trong `.venv`; lệnh không gọi API. Kết quả tại `artifacts/run_logs/phase_a_validation.log`.

`artifacts/run_logs/cp0_setup.log`: setup thật sau sửa dense search. `artifacts/run_logs/phase_a_live.log`: RAGAS 4 metrics thật. `artifacts/run_logs/phase_a_tests.log`: unit/support/schema regression 75 tests pass. `artifacts/cp0_environment.json`: môi trường, model revisions và hash corpus.

T1 nhóm đúng 20/20/10; T2 có 50 rows × 4 metric hữu hạn [0,1] và evaluator model IDs; T3 xuất đúng 10 rows tăng avg_score, đủ rank/diagnosis/fix; T4 matrix và nhóm yếu theo mean có thể đối chiếu JSON. Validation kiểm tra schema, identity/source fields, mean, matrix, bottom và hashes đầu vào.

B/C phải dùng bản `artifacts/answers_50q.json` hiện tại. Nếu sinh lại answers sau khi chạy B/C, cần chạy lại các report phụ thuộc vì hash nguồn đổi. Để kiểm tra offline dùng `python -m pytest tests/test_phase_a.py -q`. Để chấm lại từ cache đúng inputs dùng `python scripts/run_experiments.py --phase a --live`; để yêu cầu số đo mới dùng `RAGAS_REFRESH=1 python scripts/run_experiments.py --phase a --live` (có phí API).

Nguồn pipeline: repo Day 18 `K4-Track3A-DAY18-NguyenNamKhanh-2A202602568-ProductionRAG`. AI hỗ trợ: Codex hỗ trợ triển khai/debug, chạy kiểm chứng và diễn giải từ số đo thực tế. Nguyễn Nam Khánh cần review và giải thích code, dữ liệu và giới hạn khi trình bày; không coi unit mock là API experiment.
