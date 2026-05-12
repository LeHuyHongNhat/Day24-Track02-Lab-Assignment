# src/pii/anonymizer.py
import pandas as pd
import hashlib
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def _generate_fake_cccd():
    """Sinh CCCD giả 12 chữ số."""
    return "".join([str(fake.random_int(0, 9)) for _ in range(12)])


def _generate_fake_phone():
    """Sinh SĐT Việt Nam giả: 0[3|5|7|8|9] + 8 số."""
    return "0" + str(fake.random_element([3, 5, 7, 8, 9])) + \
           "".join([str(fake.random_int(0, 9)) for _ in range(8)])


class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        text = str(text)
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        operators = {}

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace",
                          {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace",
                                 {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace",
                           {"new_value": _generate_fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace",
                            {"new_value": _generate_fake_phone()}),
            }
        elif strategy == "mask":
            operators = {
                "PERSON": OperatorConfig("mask",
                          {"masking_char": "*", "chars_to_mask": 6,
                           "from_end": False}),
                "EMAIL_ADDRESS": OperatorConfig("mask",
                                 {"masking_char": "*", "chars_to_mask": 8,
                                  "from_end": False}),
                "VN_CCCD": OperatorConfig("mask",
                           {"masking_char": "*", "chars_to_mask": 8,
                            "from_end": False}),
                "VN_PHONE": OperatorConfig("mask",
                            {"masking_char": "*", "chars_to_mask": 6,
                             "from_end": False}),
            }
        elif strategy == "hash":
            operators = {
                "PERSON": OperatorConfig("hash", {"hash_type": "sha256"}),
                "EMAIL_ADDRESS": OperatorConfig("hash", {"hash_type": "sha256"}),
                "VN_CCCD": OperatorConfig("hash", {"hash_type": "sha256"}),
                "VN_PHONE": OperatorConfig("hash", {"hash_type": "sha256"}),
            }
        elif strategy == "generalize":
            operators = {
                "PERSON": OperatorConfig("replace",
                          {"new_value": fake.name().split()[-1]}),
                "EMAIL_ADDRESS": OperatorConfig("replace",
                                 {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace",
                           {"new_value": _generate_fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace",
                            {"new_value": _generate_fake_phone()}),
            }

        anonymized = self.anonymizer.anonymize(
            text=str(text),
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email, bac_si_phu_trach): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột ngay_sinh: generalize sang năm sinh
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        # Anonymize text columns
        for col in ["ho_ten", "dia_chi", "email", "bac_si_phu_trach"]:
            if col in df_anon.columns:
                df_anon[col] = df_anon[col].apply(
                    lambda x: self.anonymize_text(str(x), "replace")
                )

        # Replace CCCD and phone with fake data
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = df_anon["cccd"].apply(
                lambda x: _generate_fake_cccd()
            )

        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = df_anon["so_dien_thoai"].apply(
                lambda x: _generate_fake_phone()
            )

        # Generalize ngay_sinh to birth year
        if "ngay_sinh" in df_anon.columns:
            df_anon["ngay_sinh"] = df_anon["ngay_sinh"].apply(
                lambda x: x.split("/")[-1] if "/" in str(x) else str(x)
            )

        return df_anon

    def calculate_detection_rate(self,
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            if col not in original_df.columns:
                continue
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
