from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from oracle_control.db import get_db
from oracle_control.entities import ApprovalRecord, AuthorityRecord, CaseRecord, EventRecord, EvidenceRecord, FindingRecord
from oracle_control.security import tenant_principal

router=APIRouter(prefix="/v1/intelligence",tags=["risk and investigation intelligence"])

HIGH_SIGNAL=("permission.changed","policy.denied","credential.created","secret.accessed","data.exported","tool.invoked")
SENSITIVE=("secret","credential","customer","payment","production","private","restricted")

def event_risk(event):
    score=0;reasons=[]
    kind=event.event_type.lower()
    payload=str(event.payload).lower()
    resource=(event.resource_id or "").lower()
    if any(token in kind for token in HIGH_SIGNAL):
        score+=25;reasons.append("Event type is security-relevant")
    if any(token in resource or token in payload for token in SENSITIVE):
        score+=20;reasons.append("Sensitive resource or data indicator present")
    if event.confidence in {"inferred","unknown"}:
        score+=10;reasons.append("Relationship confidence is not directly observed")
    if event.payload.get("error_code") or event.payload.get("status_code",0) in {401,403,429}:
        score+=10;reasons.append("Source event indicates an error or access-control response")
    return min(score,100),reasons

@router.get("/risk")
def risk_overview(agent_id:str|None=None,limit:int=Query(default=500,ge=1,le=5000),
    principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    q=db.query(EventRecord).filter_by(tenant_id=principal["tenant_id"])
    if agent_id:q=q.filter_by(agent_id=agent_id)
    events=q.order_by(EventRecord.occurred_at.desc()).limit(limit).all()
    by_agent={}
    for event in events:
        key=event.agent_id or "unattributed"
        score,reasons=event_risk(event)
        bucket=by_agent.setdefault(key,{"agent_id":key,"events_considered":0,"max_event_score":0,"signals":[]})
        bucket["events_considered"]+=1
        bucket["max_event_score"]=max(bucket["max_event_score"],score)
        if score and len(bucket["signals"])<5:
            bucket["signals"].append({"event_id":event.event_id,"event_type":event.event_type,
                "occurred_at":event.occurred_at,"score":score,"reasons":reasons,
                "confidence":event.confidence})
    for bucket in by_agent.values():
        bucket["triage_level"]="high" if bucket["max_event_score"]>=50 else "moderate" if bucket["max_event_score"]>=25 else "low"
    return {"method":"transparent-rule-based-triage-v1","not_a_probability":True,
        "limitations":["Heuristic indicators are not calibrated probabilities or proof of malicious activity.",
        "Only ingested records are considered; missing source telemetry is not inferred."],
        "agents":sorted(by_agent.values(),key=lambda x:x["max_event_score"],reverse=True)}

@router.get("/cases/{case_id}/briefing")
def case_briefing(case_id:str,principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    tenant=principal["tenant_id"]
    case=db.query(CaseRecord).filter_by(id=case_id,tenant_id=tenant).first()
    if not case:raise HTTPException(404,"Case not found")
    findings=db.query(FindingRecord).filter_by(case_id=case_id,tenant_id=tenant).all()
    evidence=db.query(EvidenceRecord).filter_by(case_id=case_id,tenant_id=tenant).all()
    agent_ids={r.agent_id for r in db.query(AuthorityRecord).filter_by(tenant_id=tenant).all()}
    return {"case":{"id":case.id,"title":case.title,"severity":case.severity,"status":case.status},
        "findings":[{"id":f.id,"title":f.title,"statement":f.statement,"confidence":f.confidence,
            "evidence_ids":f.evidence_ids} for f in findings],
        "evidence":[{"id":e.id,"filename":e.filename,"sha256":e.sha256,"collected_at":e.collected_at} for e in evidence],
        "authority_records":[{"agent_id":r.agent_id,"principal_id":r.principal_id,"permission":r.permission,
            "resource_scope":r.resource_scope,"decision":r.decision,"evidence_ids":r.evidence_ids}
            for r in db.query(AuthorityRecord).filter_by(tenant_id=tenant).all() if r.agent_id in agent_ids],
        "human_approvals":[{"agent_id":r.agent_id,"approver_id":r.approver_id,"action":r.action,
            "decision":r.decision,"source_reference":r.source_reference}
            for r in db.query(ApprovalRecord).filter_by(tenant_id=tenant).all()],
        "analysis_status":"evidence_context_only",
        "limitations":["This endpoint assembles source-backed context; it does not generate an AI conclusion.",
            "Absence of a record is not proof that an action did not occur."]}
