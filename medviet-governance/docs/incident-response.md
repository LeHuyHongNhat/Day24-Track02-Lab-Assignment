# MedViet Incident Response Runbook

## Scope
Tài liệu này mô tả quy trình phản ứng khi phát hiện rò rỉ dữ liệu, truy cập trái phép, hoặc hành vi bất thường trên API.

## Severity Levels
- `SEV-1`: Lộ dữ liệu nhạy cảm, truy cập trái phép vào `raw` patient data, hoặc key bị lộ.
- `SEV-2`: Spike 403/5xx, anomaly trên API, hoặc phát hiện secret trong commit trước khi merge.
- `SEV-3`: Sự cố nhỏ, chưa có bằng chứng lộ dữ liệu nhưng cần điều tra.

## Immediate Actions
1. Xác nhận alert từ Prometheus/Grafana hoặc audit log trong `reports/api_access.log`.
2. Khoanh vùng endpoint liên quan, đặc biệt `/api/patients/raw` và `/api/patients/{patient_id}`.
3. Rotate credentials nếu nghi ngờ lộ secret hoặc KEK/DEK.
4. Tạm dừng release nếu có commit chứa dữ liệu nhạy cảm.

## 72-Hour Notification Workflow
1. Trong 0-4 giờ đầu: thu thập bằng chứng, snapshot log, và xác định phạm vi ảnh hưởng.
2. Trong 4-24 giờ: DPO đánh giá mức độ vi phạm và quyết định biện pháp khắc phục.
3. Trong 24-48 giờ: chuẩn bị báo cáo chính thức cho management, pháp chế, và đội bảo mật.
4. Trong 48-72 giờ: gửi thông báo tới cơ quan có thẩm quyền nếu sự cố đáp ứng ngưỡng báo cáo.

## Containment Checklist
- Disable token hoặc role có liên quan.
- Block source IP nếu có pattern tấn công rõ ràng.
- Rotate `.vault_key` và mọi secret dùng cho integration.
- Rebuild containers và redeploy từ commit sạch.

## Evidence to Preserve
- `reports/api_access.log`
- `reports/bandit_report.json`
- `reports/trufflehog_report.txt`
- Raw alert snapshots from Prometheus/Grafana

## Post-Incident Review
- Ghi nguyên nhân gốc.
- Cập nhật rule ở `policies/opa_policy.rego`.
- Mở follow-up task cho detection, logging, và hardening.
