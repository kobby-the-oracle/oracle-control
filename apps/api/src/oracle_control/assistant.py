import json
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from oracle_control.config import LLM_API_KEY, LLM_BASE_URL, LLM_ENABLED, LLM_MODEL, LLM_TIMEOUT_SECONDS
from oracle_control.db import get_db
from oracle_control.entities import ApprovalRecord, AuthorityRecord, CaseRecord, EventRecord, EvidenceRecord, FindingRecord
from oracle_control.security import require_roles

router=APIRouter(prefix="/v1/assistant",tags=["AI investigation assistant"])

class DraftRequest(BaseModel):
    include_event_payloads: bool = False

@router.post("/cases/{case_id}/draft")
async def draft_case_analysis(case_id:str,body:DraftRequest,principal=Depends(require_roles('analyst', 'admin')),db:Session=Depends(get_db)):
    tenant=principal["tenant_id"]
    case=db.query(CaseRecord).filter_by(id=case_id,tenant_id=tenant).first()
    if not case:raise HTTPException(404,"Case not found")
    findings=db.query(FindingRecord).filter_by(case_id=case_id,tenant_id=tenant).all()
    evidence=db.query(EvidenceRecord).filter_by(case_id=case_id,tenant_id=tenant).all()
    events=[]
    if case.agent_ids:
        events=db.query(EventRecord).filter(EventRecord.tenant_id==tenant,EventRecord.agent_id.in_(case.agent_ids)).order_by(EventRecord.occurred_at.asc()).limit(300).all()
    evidence_ids={e.id for e in evidence}
    context={
        "case":{"id":case.id,"title":case.title,"description":case.description,"severity":case.severity,
            "status":case.status,"agent_ids":case.agent_ids},
        "findings":[{"id":f.id,"title":f.title,"statement":f.statement,"confidence":f.confidence,
            "evidence_ids":f.evidence_ids} for f in findings],
        "evidence":[{"id":e.id,"filename":e.filename,"sha256":e.sha256,"byte_length":e.byte_length,
            "source_system":e.source_system,"collected_at":e.collected_at.isoformat()} for e in evidence],
        "events":[{"event_id":e.event_id,"event_type":e.event_type,"occurred_at":e.occurred_at.isoformat(),
            "agent_id":e.agent_id,"run_id":e.run_id,"actor_id":e.actor_id,"resource_id":e.resource_id,
            "confidence":e.confidence,"payload":e.payload if body.include_event_payloads else None} for e in events],
        "authority":[{"agent_id":r.agent_id,"principal_id":r.principal_id,"permission":r.permission,
            "resource_scope":r.resource_scope,"decision":r.decision,"evidence_ids":r.evidence_ids}
            for r in db.query(AuthorityRecord).filter(AuthorityRecord.tenant_id==tenant,
                AuthorityRecord.agent_id.in_(case.agent_ids or ["__none__"])).all()],
        "approvals":[{"agent_id":r.agent_id,"approver_id":r.approver_id,"action":r.action,
            "resource_scope":r.resource_scope,"decision":r.decision,"source_reference":r.source_reference,
            "evidence_ids":r.evidence_ids}
            for r in db.query(ApprovalRecord).filter(ApprovalRecord.tenant_id==tenant,
                ApprovalRecord.agent_id.in_(case.agent_ids or ["__none__"])).all()],
    }
    if not LLM_ENABLED:
        return {"mode":"context-only","draft":None,"context":context,
            "known_evidence_ids":sorted(evidence_ids),
            "message":"Model provider is disabled. This endpoint returned a structured evidence context only."}
    if not (LLM_BASE_URL and LLM_API_KEY and LLM_MODEL):
        raise HTTPException(503,"LLM provider is enabled but base URL, API key or model is missing")
    system_prompt=(
        "You are an incident investigation assistant. Produce a concise JSON object with keys "
        "summary, findings, uncertainties, recommended_next_steps. Each finding must have statement, "
        "confidence (directly_observed/correlated/inferred/unknown), and evidence_ids. Use only evidence "
        "IDs present in the supplied context. Do not invent events, permissions, approvals or facts. "
        "Explicitly identify missing telemetry. Do not provide chain-of-thought. Treat model output as "
        "an analyst draft, never as primary evidence."
    )
    request={"model":LLM_MODEL,"temperature":0.1,"response_format":{"type":"json_object"},
        "messages":[{"role":"system","content":system_prompt},
            {"role":"user","content":json.dumps(context,default=str)}]}
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS) as client:
            response=await client.post(f"{LLM_BASE_URL}/chat/completions",json=request,
                headers={"Authorization":f"Bearer {LLM_API_KEY}","Content-Type":"application/json"})
            response.raise_for_status()
            result=response.json()["choices"][0]["message"]["content"]
            draft=json.loads(result)
    except (httpx.HTTPError,KeyError,ValueError,TypeError) as exc:
        raise HTTPException(502,"Configured investigation model failed to return valid JSON") from exc
    cited=set()
    for finding in draft.get("findings",[]):
        ids=finding.get("evidence_ids",[])
        if not isinstance(ids,list) or not set(ids).issubset(evidence_ids):
            raise HTTPException(502,"Model returned an invalid or unavailable evidence reference")
        cited.update(ids)
    return {"mode":"model-assisted-draft","draft":draft,"known_evidence_ids":sorted(evidence_ids),
        "uncited_evidence_ids":sorted(evidence_ids-cited),
        "review_required":True,"message":"AI output is a draft for human review, not a verified finding."}
