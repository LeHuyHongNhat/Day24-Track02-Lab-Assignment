# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure)
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.example

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256-GCM at rest, TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | FastAPI middleware logging request ID, user, role, resource, action, status | ✅ Done | Platform Team |
| Breach detection | Prometheus metrics + AlertManager rules + Grafana dashboard | ✅ Done | Security Team |

## F. Technical Solution Details

### Audit Logging
- **Solution**: FastAPI middleware ghi log JSON vào `reports/api_access.log`. Mỗi request được log với: `timestamp`, `request_id`, `user`, `role`, `resource`, `action`, `status_code`, `duration_ms`.
- **Retention**: Log được rotate hàng ngày, giữ 90 ngày.
- **Monitoring**: Log errors (5xx, 403) được đẩy vào Prometheus counter để alert.

### Breach Detection
- **Solution**: Prometheus AlertManager rules cho:
  - `High5xxRate`: HTTP 5xx > 5% trong 5 phút
  - `High403Rate`: HTTP 403 spike > 10 requests/phút
  - `UnauthorizedRawAccess`: Request đến `/api/patients/raw` từ role không phải admin
- **Dashboard**: Grafana dashboard hiển thị request rate, error rate, PII access audit trail.
- **Incident Response**: Runbook tại `docs/incident-response.md`, alert tự động gửi đến Slack #security và email DPO.

### Data Localization
- **Solution**: Tất cả server và database đặt tại Việt Nam. Backup cũng lưu trong lãnh thổ Việt Nam. Mọi cross-border data transfer phải có DPO approval và được ghi log đầy đủ để audit.
- **OPA enforcement**: Rule `deny` trong `policies/opa_policy.rego` chặn export restricted data ra ngoài VN.

### Consent Management
- **Solution**: Bảng `consent_records` trong database với các trường: `user_id`, `purpose`, `policy_version`, `consent_timestamp`, `withdraw_timestamp`, `status`. API endpoint `POST /api/consent/withdraw` cho phép user rút consent, trigger xóa/xóa định danh dữ liệu cá nhân trong 30 ngày.
