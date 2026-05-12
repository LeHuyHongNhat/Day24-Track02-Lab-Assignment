import asyncio
import json

import pytest
from fastapi import HTTPException

from src.access.rbac import get_current_user
from src.api.main import (
    delete_patient,
    get_aggregated_metrics,
    get_anonymized_patients,
    get_raw_patients,
)


class TestRBACApi:
    def test_raw_patients_requires_token(self):
        with pytest.raises(HTTPException) as exc:
            get_current_user(None)
        assert exc.value.status_code == 401

    def test_raw_patients_rejects_invalid_token(self):
        with pytest.raises(HTTPException) as exc:
            get_current_user("Bearer invalid-token")
        assert exc.value.status_code == 401

    def test_raw_patients_denies_ml_engineer(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_raw_patients(current_user={"username": "bob", "role": "ml_engineer"}))
        assert exc.value.status_code == 403

    def test_raw_patients_allows_admin(self):
        response = asyncio.run(get_raw_patients(current_user={"username": "alice", "role": "admin"}))
        payload = json.loads(response.body)
        assert response.status_code == 200
        assert isinstance(payload, list)
        assert len(payload) == 10

    def test_anonymized_patients_allows_ml_engineer(self):
        response = asyncio.run(
            get_anonymized_patients(current_user={"username": "bob", "role": "ml_engineer"})
        )
        payload = json.loads(response.body)
        assert response.status_code == 200
        assert isinstance(payload, list)
        assert len(payload) == 10

    def test_delete_patient_denies_ml_engineer(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(delete_patient(patient_id="abc123", current_user={"username": "bob", "role": "ml_engineer"}))
        assert exc.value.status_code == 403

    def test_aggregated_metrics_allows_data_analyst(self):
        response = asyncio.run(
            get_aggregated_metrics(current_user={"username": "carol", "role": "data_analyst"})
        )
        payload = json.loads(response.body)
        assert response.status_code == 200
        assert payload["total_patients"] > 0
        assert "by_condition" in payload
        assert "test_result" in payload
