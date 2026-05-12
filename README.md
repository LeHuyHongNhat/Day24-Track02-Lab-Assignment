# Lab Assignment: Data Governance & Security for AI Platform

**Course:** AICB-P2T2 · Lab #24 Extended
**Thời gian:** 3–4 giờ
**Hình thức:** Cá nhân hoặc nhóm 2 người

---

## Bối Cảnh (Scenario)

> Bạn vừa được tuyển vào team AI của **MedViet** — một startup y tế Việt Nam xử lý hồ sơ bệnh nhân để train mô hình chẩn đoán bệnh. Công ty đang chuẩn bị ký hợp đồng với đối tác doanh nghiệp lớn và cần đạt chuẩn **NĐ13/ISO 27001**. Nhiệm vụ của bạn là xây dựng toàn bộ data governance pipeline từ đầu.

---

## Cấu Trúc Project

```
medviet-governance/
├── data/
│   ├── raw/
│   │   └── patients_raw.csv          # Dữ liệu gốc có PII
│   └── processed/
│       └── patients_anonymized.csv   # Output sau anonymization
├── src/
│   ├── pii/
│   │   ├── detector.py               # Presidio recognizers
│   │   └── anonymizer.py             # Anonymization pipeline
│   ├── access/
│   │   ├── rbac.py                   # Casbin RBAC
│   │   └── policy.csv                # Role policies
│   ├── encryption/
│   │   └── vault.py                  # Encrypt/decrypt utils
│   ├── quality/
│   │   └── validation.py             # Great Expectations
│   └── api/
│       └── main.py                   # FastAPI với RBAC
├── policies/
│   └── opa_policy.rego               # OPA access rules
├── tests/
│   └── test_pii.py
├── .github/
│   └── hooks/
│       └── pre-commit                # git-secrets hook
├── docker-compose.yml                # MLflow + Prometheus + Grafana
└── requirements.txt
```

---

## Phần 1 — Chuẩn Bị Dữ Liệu (15 phút)

### 1.1 Tạo Dataset Giả Lập

Tạo file `data/raw/patients_raw.csv` bằng script sau:

```python
# scripts/generate_data.py
import pandas as pd
from faker import Faker
import random

fake = Faker("vi_VN")
Faker.seed(42)

def generate_patients(n=200):
    records = []
    for _ in range(n):
        records.append({
            "patient_id": fake.uuid4(),
            "ho_ten": fake.name(),
            "cccd": f"{random.randint(0,9)}" + 
                    "".join([str(random.randint(0,9)) for _ in range(11)]),
            "ngay_sinh": fake.date_of_birth(minimum_age=18, maximum_age=90)
                              .strftime("%d/%m/%Y"),
            "so_dien_thoai": f"0{random.choice([3,5,7,8,9])}" + 
                              "".join([str(random.randint(0,9)) for _ in range(8)]),
            "email": fake.email(),
            "dia_chi": fake.address(),
            "benh": random.choice(["Tiểu đường", "Huyết áp cao", 
                                   "Tim mạch", "Khỏe mạnh"]),
            "ket_qua_xet_nghiem": round(random.uniform(3.5, 12.0), 2),
            "bac_si_phu_trach": fake.name(),
            "ngay_kham": fake.date_this_year().strftime("%d/%m/%Y"),
        })
    return pd.DataFrame(records)

df = generate_patients()
df.to_csv("data/raw/patients_raw.csv", index=False)
print(f"Generated {len(df)} patient records")
print(df.head(3))
```

**Yêu cầu:** Chạy script và kiểm tra dữ liệu đầu ra. Liệt kê tất cả các cột chứa PII.

---

## Phần 2 — PII Detection & Anonymization (45 phút)

### 2.1 Cài Đặt

```bash
pip install presidio-analyzer presidio-anonymizer spacy faker
python -m spacy download vi_core_news_lg  # Vietnamese NER model
```

### 2.2 Xây Dựng Custom Recognizers cho Tiếng Việt

Hoàn thành file `src/pii/detector.py`:

```python
# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

def build_vietnamese_analyzer() -> AnalyzerEngine:
    """
    TODO: Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN.
    """

    # --- TASK 2.2.1 ---
    # Tạo CCCD recognizer: số CCCD VN có đúng 12 chữ số
    cccd_pattern = Pattern(
        name="cccd_pattern",
        regex=r"___",          # TODO: điền regex cho 12 chữ số
        score=0.9
    )
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[cccd_pattern],
        context=["cccd", "căn cước", "chứng minh", "cmnd"]
    )

    # --- TASK 2.2.2 ---
    # Tạo phone recognizer: số điện thoại VN (0[3|5|7|8|9]xxxxxxxx)
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern(
            name="vn_phone",
            regex=r"___",      # TODO: điền regex
            score=0.85
        )],
        context=["điện thoại", "sdt", "phone", "liên hệ"]
    )

    # --- TASK 2.2.3 ---
    # Tạo NLP engine dùng spaCy Vietnamese model
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "vi", 
                    "model_name": "___"}]   # TODO: điền model name
    })
    nlp_engine = provider.create_engine()

    # --- TASK 2.2.4 ---
    # Khởi tạo AnalyzerEngine và add các recognizer
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    analyzer.registry.add_recognizer(___)   # TODO
    analyzer.registry.add_recognizer(___)   # TODO

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """
    TODO: Detect PII trong text tiếng Việt.
    Trả về list các RecognizerResult.
    Entities cần detect: PERSON, EMAIL_ADDRESS, VN_CCCD, VN_PHONE
    """
    results = analyzer.analyze(
        text=___,       # TODO
        language=___,   # TODO
        entities=___    # TODO
    )
    return results
```

### 2.3 Xây Dựng Anonymization Pipeline

Hoàn thành file `src/pii/anonymizer.py`:

```python
# src/pii/anonymizer.py
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        TODO: Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        # TODO: implement operators dict dựa trên strategy
        operators = {}

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", 
                          {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", 
                                 {"new_value": ___}),   # TODO: fake email
                "VN_CCCD": OperatorConfig("replace", 
                           {"new_value": ___}),          # TODO: fake CCCD
                "VN_PHONE": OperatorConfig("replace", 
                            {"new_value": ___}),         # TODO: fake phone
            }
        elif strategy == "mask":
            # TODO: implement masking
            pass
        elif strategy == "hash":
            # TODO: implement hashing dùng sha256
            pass

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TODO: Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        # TODO: Xử lý từng cột PII
        # Gợi ý: dùng df.apply() hoặc list comprehension

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        TODO: Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
```

### 2.4 Test Anonymization

```python
# tests/test_pii.py
import pytest
import pandas as pd
from src.pii.anonymizer import MedVietAnonymizer

@pytest.fixture
def anonymizer():
    return MedVietAnonymizer()

@pytest.fixture
def sample_df():
    return pd.read_csv("data/raw/patients_raw.csv").head(50)

class TestPIIDetection:

    def test_cccd_detected(self, anonymizer):
        text = "Bệnh nhân Nguyen Van A, CCCD: 012345678901"
        results = anonymizer.analyzer.analyze(text=text, language="vi",
                                               entities=["VN_CCCD"])
        # TODO: assert rằng có ít nhất 1 result
        assert ___

    def test_phone_detected(self, anonymizer):
        text = "Liên hệ: 0912345678"
        # TODO: viết test tương tự
        pass

    def test_email_detected(self, anonymizer):
        text = "Email: nguyenvana@gmail.com"
        # TODO: viết test
        pass

    # --- TASK QUAN TRỌNG ---
    def test_detection_rate_above_95_percent(self, anonymizer, sample_df):
        """Pipeline phải đạt >95% detection rate."""
        pii_columns = ["ho_ten", "cccd", "so_dien_thoai", "email"]
        rate = anonymizer.calculate_detection_rate(sample_df, pii_columns)
        print(f"\nDetection rate: {rate:.2%}")
        assert rate >= 0.95, f"Detection rate {rate:.2%} < 95%"

class TestAnonymization:

    def test_pii_not_in_output(self, anonymizer, sample_df):
        """Sau anonymization, không còn CCCD gốc trong output."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        for original_cccd in sample_df["cccd"]:
            # TODO: assert CCCD gốc không xuất hiện trong df_anon
            assert str(original_cccd) not in ___

    def test_non_pii_columns_unchanged(self, anonymizer, sample_df):
        """Cột benh và ket_qua_xet_nghiem phải giữ nguyên."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        # TODO: assert hai cột này không thay đổi
        pass
```

**Chạy test:**

```bash
pytest tests/test_pii.py -v --tb=short
```

---

## Phần 3 — RBAC với Casbin & FastAPI (45 phút)

### 3.1 Định Nghĩa Policy

Tạo file `src/access/policy.csv`:

```csv
# Format: p, role, resource, action
p, admin, patient_data, read
p, admin, patient_data, write
p, admin, patient_data, delete
p, admin, model_artifacts, read
p, admin, model_artifacts, write

p, ml_engineer, training_data, read
p, ml_engineer, model_artifacts, read
p, ml_engineer, model_artifacts, write
# TODO: ml_engineer KHÔNG được delete production data
# TODO: ml_engineer KHÔNG được đọc raw PII

p, data_analyst, aggregated_metrics, read
p, data_analyst, reports, write
# TODO: data_analyst KHÔNG được đọc raw PII

p, intern, sandbox_data, read
p, intern, sandbox_data, write
# TODO: intern KHÔNG được access production

# Role inheritance
g, alice, admin
g, bob, ml_engineer
g, carol, data_analyst
g, dave, intern
```

Tạo file `src/access/model.conf`:

```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

### 3.2 RBAC Module

Hoàn thành `src/access/rbac.py`:

```python
# src/access/rbac.py
import casbin
from functools import wraps
from fastapi import HTTPException, Header
from typing import Optional

# Danh sách user giả lập (production dùng JWT + DB)
MOCK_USERS = {
    "token-alice": {"username": "alice", "role": "admin"},
    "token-bob":   {"username": "bob",   "role": "ml_engineer"},
    "token-carol": {"username": "carol", "role": "data_analyst"},
    "token-dave":  {"username": "dave",  "role": "intern"},
}

enforcer = casbin.Enforcer("src/access/model.conf", "src/access/policy.csv")

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    TODO: Parse Bearer token và trả về user info.
    Raise HTTPException 401 nếu token không hợp lệ.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=___, detail="Missing token")

    token = authorization.split(" ")[1]
    user = MOCK_USERS.get(token)

    if not user:
        raise HTTPException(status_code=___, detail="Invalid token")

    return user

def require_permission(resource: str, action: str):
    """
    TODO: Decorator kiểm tra RBAC permission.
    Dùng casbin enforcer để check (role, resource, action).
    Raise HTTPException 403 nếu không có quyền.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Lấy current_user từ kwargs (FastAPI inject qua Depends)
            current_user = kwargs.get("current_user")
            role = current_user["role"]

            allowed = enforcer.enforce(___, ___, ___)  # TODO

            if not allowed:
                raise HTTPException(
                    status_code=___,    # TODO: HTTP status code
                    detail=f"Role '{role}' cannot '{action}' on '{resource}'"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 3.3 FastAPI với RBAC

Hoàn thành `src/api/main.py`:

```python
# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    pass

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    pass

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    pass

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Chỉ admin được xóa. Các role khác nhận 403.
    """
    pass

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
```

**Chạy và test:**

```bash
uvicorn src.api.main:app --reload

# Test với curl
curl -H "Authorization: Bearer token-bob" http://localhost:8000/api/patients/raw
# → Phải trả về 403 (bob là ml_engineer, không được đọc raw PII)

curl -H "Authorization: Bearer token-alice" http://localhost:8000/api/patients/raw
# → Phải trả về 200 (alice là admin)

curl -X DELETE -H "Authorization: Bearer token-bob" \
     http://localhost:8000/api/patients/abc123
# → Phải trả về 403
```

---

## Phần 4 — Encryption (30 phút)

### 4.1 Implement Encryption Vault

Hoàn thành `src/encryption/vault.py`:

```python
# src/encryption/vault.py
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class SimpleVault:
    """
    Mô phỏng envelope encryption pattern (thay thế AWS KMS cho local dev).
    
    Architecture:
        Master Key (KEK) → encrypts → Data Key (DEK) → encrypts → Data
    """

    def __init__(self, master_key_path: str = ".vault_key"):
        self.master_key_path = master_key_path
        self.kek = self._load_or_create_kek()

    def _load_or_create_kek(self) -> bytes:
        """
        TODO: Load KEK từ file nếu tồn tại, 
              ngược lại generate 32-byte random key và lưu vào file.
        QUAN TRỌNG: Trong production, KEK phải lưu trong HSM/KMS, không phải file.
        """
        if os.path.exists(self.master_key_path):
            with open(self.master_key_path, "rb") as f:
                return base64.b64decode(f.read())
        else:
            kek = os.urandom(32)  # 256-bit key
            with open(self.master_key_path, "wb") as f:
                f.write(base64.b64encode(kek))
            return kek

    def generate_dek(self) -> tuple[bytes, bytes]:
        """
        TODO: Generate một Data Encryption Key (DEK) mới.
        Trả về (plaintext_dek, encrypted_dek).
        Dùng AESGCM để encrypt DEK bằng KEK.
        """
        plaintext_dek = os.urandom(32)

        # Encrypt DEK bằng KEK
        aesgcm = AESGCM(self.kek)
        nonce = os.urandom(12)
        encrypted_dek = nonce + aesgcm.encrypt(nonce, plaintext_dek, None)

        return plaintext_dek, encrypted_dek

    def decrypt_dek(self, encrypted_dek: bytes) -> bytes:
        """
        TODO: Decrypt encrypted DEK bằng KEK.
        Trả về plaintext DEK.
        """
        nonce = encrypted_dek[:12]
        ciphertext = encrypted_dek[12:]
        aesgcm = AESGCM(self.kek)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def encrypt_data(self, plaintext: str) -> dict:
        """
        TODO: Implement envelope encryption.
        1. Generate DEK mới
        2. Encrypt data bằng plaintext DEK
        3. Xóa plaintext DEK khỏi memory
        4. Trả về dict chứa encrypted_dek và ciphertext (base64 encoded)
        
        Return format:
        {
            "encrypted_dek": "<base64>",
            "ciphertext": "<base64>",
            "algorithm": "AES-256-GCM"
        }
        """
        plaintext_dek, encrypted_dek = self.generate_dek()

        # TODO: encrypt data bằng plaintext_dek
        aesgcm = AESGCM(plaintext_dek)
        nonce = os.urandom(12)
        ciphertext = ___   # TODO

        # Xóa plaintext DEK
        del plaintext_dek

        return {
            "encrypted_dek": base64.b64encode(encrypted_dek).decode(),
            "ciphertext": base64.b64encode(nonce + ciphertext).decode(),
            "algorithm": "AES-256-GCM"
        }

    def decrypt_data(self, encrypted_payload: dict) -> str:
        """
        TODO: Decrypt data từ envelope encryption payload.
        1. Decrypt DEK bằng KEK
        2. Decrypt data bằng DEK
        3. Trả về plaintext string
        """
        encrypted_dek = base64.b64decode(encrypted_payload["encrypted_dek"])
        ciphertext_with_nonce = base64.b64decode(encrypted_payload["ciphertext"])

        # TODO: implement decryption
        plaintext_dek = ___   # TODO
        nonce = ___           # TODO (first 12 bytes)
        ciphertext = ___      # TODO (remaining bytes)

        aesgcm = AESGCM(plaintext_dek)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        del plaintext_dek

        return plaintext.decode()

    def encrypt_column(self, df, column: str) -> pd.DataFrame:
        """
        TODO: Encrypt một cột trong DataFrame.
        Thay thế giá trị gốc bằng JSON string của encrypted payload.
        """
        import json
        df = df.copy()
        df[column] = df[column].apply(
            lambda x: json.dumps(self.encrypt_data(str(x)))
        )
        return df
```

**Test encryption:**

```python
# Chạy trong Python shell
from src.encryption.vault import SimpleVault
vault = SimpleVault()

# Test round-trip
original = "Nguyen Van A - CCCD: 012345678901"
encrypted = vault.encrypt_data(original)
print("Encrypted:", encrypted)

decrypted = vault.decrypt_data(encrypted)
print("Decrypted:", decrypted)
assert decrypted == original, "Encryption round-trip FAILED!"
print("✓ Encryption test passed")
```

---

## Phần 5 — Data Quality Validation (20 phút)

### 5.1 Great Expectations Validation Suite

Hoàn thành `src/quality/validation.py`:

```python
# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite

def build_patient_expectation_suite() -> ExpectationSuite:
    """
    TODO: Tạo expectation suite cho anonymized patient data.
    """
    context = gx.get_context()
    suite = context.add_expectation_suite("patient_data_suite")

    # Lấy validator
    df = pd.read_csv("data/raw/patients_raw.csv")
    validator = context.sources.pandas_default.read_dataframe(df)

    # --- TASK: Thêm các expectations ---

    # 1. patient_id không được null
    validator.expect_column_values_to_not_be_null("patient_id")

    # 2. TODO: cccd phải có đúng 12 ký tự
    validator.expect_column_value_lengths_to_equal(
        column=___,
        value=___
    )

    # 3. TODO: ket_qua_xet_nghiem phải trong khoảng [0, 50]
    validator.expect_column_values_to_be_between(
        column=___,
        min_value=___,
        max_value=___
    )

    # 4. TODO: benh phải thuộc danh sách hợp lệ
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    validator.expect_column_values_to_be_in_set(
        column=___,
        value_set=___
    )

    # 5. TODO: email phải match regex pattern
    validator.expect_column_values_to_match_regex(
        column="email",
        regex=r"___"    # TODO: email regex
    )

    # 6. TODO: Không được có duplicate patient_id
    validator.expect_column_values_to_be_unique(column=___)

    validator.save_expectation_suite()
    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
    TODO: Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD gốc dạng số thuần túy
    # (sau anonymization, cccd phải là fake hoặc masked)
    # TODO: implement check

    # Check 2: Không có null values trong các cột quan trọng
    # TODO: implement check

    # Check 3: Số rows phải bằng original
    # TODO: implement check

    return results
```

---

## Phần 6 — Security Scanning (20 phút)

### 6.1 Setup Git-Secrets Hook

```bash
# Cài đặt git-secrets
brew install git-secrets   # macOS
# hoặc: sudo apt-get install git-secrets

# Init trong project
cd medviet-governance
git init
git secrets --install

# Thêm patterns cho VN context
git secrets --add 'CCCD[:\s]+\d{12}'
git secrets --add 'cccd[:\s]+\d{12}'
git secrets --add 'password\s*=\s*["\'][^"\']+["\']'
git secrets --add 'secret_key\s*=\s*["\'][^"\']+["\']'

# Thêm AWS patterns
git secrets --register-aws
```

**Tạo file `.github/hooks/pre-commit`:**

```bash
#!/bin/bash
# Pre-commit hook: chạy security checks trước khi commit

echo "🔍 Running security checks..."

# 1. git-secrets scan
git secrets --pre_commit_hook -- "$@"
if [ $? -ne 0 ]; then
    echo "❌ git-secrets found potential secrets! Commit blocked."
    exit 1
fi

# 2. Bandit SAST scan
echo "🐍 Running Bandit SAST..."
bandit -r src/ -ll -q
if [ $? -ne 0 ]; then
    echo "❌ Bandit found security issues! Review above."
    exit 1
fi

# 3. pip-audit dependency check
echo "📦 Checking dependencies for CVEs..."
pip-audit --desc on
if [ $? -ne 0 ]; then
    echo "⚠️  Vulnerable dependencies found! Update before committing."
    exit 1
fi

echo "✅ All security checks passed!"
exit 0
```

```bash
chmod +x .github/hooks/pre-commit
cp .github/hooks/pre-commit .git/hooks/pre-commit
```

### 6.2 TruffleHog Scan

```bash
# Scan toàn bộ repo history
trufflehog git file://. --only-verified

# Scan chỉ staged files
trufflehog git file://. --since-commit HEAD~1 --only-verified
```

**Task:** Cố tình commit một file có chứa fake credential rồi verify rằng hook block được:

```python
# ĐỪNG commit file này — chỉ để test hook
# test_secret.py
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"   # fake
```

### 6.3 Bandit SAST Scan

```bash
pip install bandit

# Scan src/ với medium severity trở lên
bandit -r src/ -ll

# Export báo cáo
bandit -r src/ -f json -o reports/bandit_report.json
```

**Tạo thư mục reports và lưu scan results.**

---

## Phần 7 — OPA Policy (15 phút)

Tạo `policies/opa_policy.rego`:

```rego
package medviet.data_access

import future.keywords.if
import future.keywords.in

# Default: deny all
default allow := false

# Admin được phép tất cả
allow if {
    input.user.role == "admin"
}

# ML Engineer được đọc training data và model artifacts
allow if {
    input.user.role == "ml_engineer"
    input.resource in {"training_data", "model_artifacts"}
    input.action in {"read", "write"}
}

# TODO: ML Engineer KHÔNG được delete production data
deny if {
    input.user.role == "ml_engineer"
    input.resource == "production_data"
    input.action == "delete"
}

# TODO: Data Analyst chỉ được đọc aggregated metrics và viết reports
allow if {
    input.user.role == "data_analyst"
    # Hoàn thành rule này
}

# TODO: Intern chỉ được access sandbox
allow if {
    input.user.role == "intern"
    # Hoàn thành rule này
}

# Rule: không ai được export restricted data ra ngoài VN servers
deny if {
    input.data_classification == "restricted"
    input.destination_country != "VN"
}
```

**Test OPA policy:**

```bash
# Cài OPA
brew install opa

# Test ml_engineer không được delete
echo '{
  "user": {"role": "ml_engineer"},
  "resource": "production_data",
  "action": "delete"
}' | opa eval -d policies/opa_policy.rego -I "data.medviet.data_access.allow"
# Expected: false
```

---

## Phần 8 — Compliance Checklist (15 phút)

Tạo file `compliance_checklist.md`:

```markdown
# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [ ] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [ ] Backup cũng phải ở trong lãnh thổ VN
- [ ] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [ ] Thu thập consent trước khi dùng data cho AI training
- [ ] Có mechanism để user rút consent (Right to Erasure)
- [ ] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [ ] Có incident response plan
- [ ] Alert tự động khi phát hiện breach
- [ ] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [ ] Đã bổ nhiệm Data Protection Officer
- [ ] DPO có thể liên hệ tại: ___

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256 at rest, TLS 1.3 in transit | 🚧 In Progress | Infra Team |
| Audit logging | CloudTrail + API access logs | ⬜ Todo | Platform Team |
| Breach detection | Anomaly monitoring (Prometheus) | ⬜ Todo | Security Team |

## F. TODO: Điền vào phần còn thiếu
Với mỗi row còn "⬜ Todo", mô tả technical solution cụ thể bạn sẽ implement.
```

---

## Deliverables & Chấm Điểm

| Hạng mục | Điểm | Tiêu chí |
|---------|------|---------|
| **PII Detection** | 25đ | Detection rate ≥ 95% trên test data; CCCD + phone + email đều detect được |
| **Anonymization** | 20đ | PII gốc không còn trong output; non-PII columns giữ nguyên |
| **RBAC API** | 20đ | 3 roles hoạt động đúng; 403 đúng chỗ; tests pass |
| **Encryption** | 15đ | Envelope encryption round-trip thành công; không lưu plaintext key |
| **Security Audit** | 10đ | git-secrets hook chặn được credential; Bandit report có |
| **Compliance Checklist** | 10đ | NĐ13 mapping đầy đủ, technical controls cụ thể |

**Tổng: 100đ** — Pass: ≥ 70đ

---

## Quick Commands

Nếu bạn muốn chạy nhanh bằng `make`, dùng các target trong `medviet-governance/Makefile`:

```bash
cd medviet-governance
make data       # tạo lại data/raw/patients_raw.csv và data/processed/patients_anonymized.csv
make test       # chạy pytest và ghi reports/test_results.txt
make bandit     # chạy Bandit và ghi reports/bandit_report.json
make trufflehog # scan git history và ghi reports/trufflehog_report.txt
make report     # chạy test + security checks
make package    # tạo lab24_submission_<ten_sv>.zip
```

Ghi chú:

- `make security` chạy `bandit` + `trufflehog`.
- `make audit` thử chạy `pip-audit` nếu binary có sẵn trong `.venv`.
- `make clean` xóa các báo cáo và file zip đã tạo.

---

## Nộp Bài

```bash
# Tạo báo cáo tổng hợp
mkdir -p reports
pytest tests/ -v --tb=short > reports/test_results.txt
bandit -r src/ -f json -o reports/bandit_report.json
trufflehog git file://. --only-verified > reports/trufflehog_report.txt

# Nộp
zip -r lab24_submission_<ten_sv>.zip \
    src/ tests/ policies/ data/processed/ \
    compliance_checklist.md reports/ requirements.txt
```

> **Lưu ý:** KHÔNG nộp file `data/raw/`, `.vault_key`, hoặc bất kỳ file nào chứa credentials thật.
