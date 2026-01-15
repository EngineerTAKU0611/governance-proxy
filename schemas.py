import hashlib
import json
import time
from typing import Literal
from pydantic import BaseModel, Field

class ExecutionIntent(BaseModel):
    purpose: Literal["research", "production", "debug", "demo", "other"]
    description: str

class RiskAssessment(BaseModel):
    estimated_cost_usd: float
    risk_level: Literal["low", "medium", "high", "critical"]
    budget_impact_percent: float

class ImmutableLog(BaseModel):
    execution_id: str
    requester_id: str
    budget_owner_id: str
    timestamp_utc: float = Field(default_factory=time.time)
    
    intent: ExecutionIntent
    risk_assessment: RiskAssessment
    target_url: str
    request_body_hash: str
    log_hash: str = ""

    def compute_canonical_hash(self) -> str:
        data = self.model_dump(exclude={'log_hash'})
        canonical_json = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()