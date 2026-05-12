# src/quality/validation.py
import pandas as pd
import re


def build_patient_expectation_suite():
    """
    Tạo expectation suite cho anonymized patient data.
    """
    import great_expectations as gx

    context = gx.get_context()
    suite = context.add_expectation_suite("patient_data_suite")

    df = pd.read_csv("data/raw/patients_raw.csv")
    validator = context.sources.pandas_default.read_dataframe(df)

    # 1. patient_id không được null
    validator.expect_column_values_to_not_be_null("patient_id")

    # 2. cccd phải có đúng 12 ký tự
    validator.expect_column_value_lengths_to_equal(
        column="cccd",
        value=12
    )

    # 3. ket_qua_xet_nghiem phải trong khoảng [0, 50]
    validator.expect_column_values_to_be_between(
        column="ket_qua_xet_nghiem",
        min_value=0,
        max_value=50
    )

    # 4. benh phải thuộc danh sách hợp lệ
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    validator.expect_column_values_to_be_in_set(
        column="benh",
        value_set=valid_conditions
    )

    # 5. email phải match regex pattern
    validator.expect_column_values_to_match_regex(
        column="email",
        regex=r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
    )

    # 6. Không được có duplicate patient_id
    validator.expect_column_values_to_be_unique(column="patient_id")

    validator.save_expectation_suite()
    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
    Validate anonymized data.
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

    # Load raw data once for comparison
    raw_path = "data/raw/patients_raw.csv"
    raw_df = None
    try:
        raw_df = pd.read_csv(raw_path)
        results["stats"]["raw_rows"] = len(raw_df)
    except FileNotFoundError:
        results["failed_checks"].append("Raw data file not found for comparison")

    # Check 1: CCCD gốc không xuất hiện trong anonymized data
    if raw_df is not None and "cccd" in raw_df.columns and "cccd" in df.columns:
        raw_cccds = set(raw_df["cccd"].astype(str))
        for idx, val in df["cccd"].items():
            if str(val) in raw_cccds:
                results["failed_checks"].append(
                    f"Row {idx}: Original CCCD leaked: {val}"
                )

    # Check 2: Không có null values trong các cột quan trọng
    critical_cols = ["patient_id", "benh", "ket_qua_xet_nghiem"]
    for col in critical_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                results["failed_checks"].append(
                    f"Column '{col}' has {null_count} null values"
                )

    # Check 3: Số rows phải bằng original
    if raw_df is not None and len(df) != len(raw_df):
        results["failed_checks"].append(
            f"Row count mismatch: anonymized={len(df)}, raw={len(raw_df)}"
        )

    if results["failed_checks"]:
        results["success"] = False

    return results
