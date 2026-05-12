# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.api.observability import install_observability, render_prometheus_metrics
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()
install_observability(app)


def _load_raw_df():
    return pd.read_csv("data/raw/patients_raw.csv")


# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    df = _load_raw_df()
    return JSONResponse(content=df.head(10).to_dict(orient="records"))


# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    df = _load_raw_df().head(10)
    df_anon = anonymizer.anonymize_dataframe(df)
    return JSONResponse(content=df_anon.to_dict(orient="records"))


# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    df = _load_raw_df()
    count_by_benh = df["benh"].value_counts().to_dict()
    stats = {
        "total_patients": len(df),
        "by_condition": count_by_benh,
        "test_result": {
            "min": float(df["ket_qua_xet_nghiem"].min()),
            "max": float(df["ket_qua_xet_nghiem"].max()),
            "avg": round(float(df["ket_qua_xet_nghiem"].mean()), 2)
        }
    }
    return JSONResponse(content=stats)


# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403.
    """
    return JSONResponse(content={
        "status": "deleted",
        "patient_id": patient_id,
        "message": f"Patient {patient_id} has been deleted (simulated)"
    })


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(
        render_prometheus_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
