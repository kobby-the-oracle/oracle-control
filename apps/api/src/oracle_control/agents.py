from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from oracle_control.db import get_db
from oracle_control.entities import AgentRecord, AuditRecord, EventRecord
from oracle_control.security import tenant_principal

router=APIRouter(prefix="/v1/agents",tags=["agent intelligence"])

class AgentUpsert(BaseModel):
    agent_id:str=Field(min_length=1,max_length=256)
    display_name:str=Field(min_length=1,max_length=256)
    framework:str|None=None
    environment:str|None=None
    owner:str|None=None
    metadata:dict=Field(default_factory=dict)

@router.post("",status_code=201)
def register_agent(body:AgentUpsert,principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    tenant=principal["tenant_id"]
    row=db.query(AgentRecord).filter_by(tenant_id=tenant,agent_id=body.agent_id).first()
    if row:
        row.display_name=body.display_name;row.framework=body.framework;row.environment=body.environment
        row.owner=body.owner;row.metadata_json=body.metadata
        action="agent.updated"
    else:
        row=AgentRecord(tenant_id=tenant,agent_id=body.agent_id,display_name=body.display_name,
            framework=body.framework,environment=body.environment,owner=body.owner,metadata_json=body.metadata)
        db.add(row);action="agent.registered"
    db.add(AuditRecord(tenant_id=tenant,actor=principal["subject"],action=action,
        object_type="agent",object_id=body.agent_id,details={"framework":body.framework}))
    db.commit()
    return {"agent_id":row.agent_id,"display_name":row.display_name,"framework":row.framework,
        "environment":row.environment,"owner":row.owner,"status":row.status}

@router.get("")
def list_agents(principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    tenant=principal["tenant_id"]
    registered=db.query(AgentRecord).filter_by(tenant_id=tenant).all()
    seen={r.agent_id:r for r in registered}
    events=db.query(EventRecord).filter_by(tenant_id=tenant).filter(EventRecord.agent_id.is_not(None)).all()
    for event in events:
        if event.agent_id not in seen: seen[event.agent_id]=None
    result=[]
    for agent_id,row in seen.items():
        matching=[e for e in events if e.agent_id==agent_id]
        result.append({"agent_id":agent_id,"display_name":row.display_name if row else agent_id,
            "framework":row.framework if row else None,"environment":row.environment if row else None,
            "owner":row.owner if row else None,"status":row.status if row else "observed-unregistered",
            "event_count":len(matching),"last_seen":max((e.occurred_at for e in matching),default=None)})
    return result

@router.get("/{agent_id}")
def get_agent(agent_id:str,principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    tenant=principal["tenant_id"]
    row=db.query(AgentRecord).filter_by(tenant_id=tenant,agent_id=agent_id).first()
    events=db.query(EventRecord).filter_by(tenant_id=tenant,agent_id=agent_id).order_by(EventRecord.occurred_at.desc()).limit(100).all()
    if not row and not events: raise HTTPException(404,"Agent not found")
    return {"agent_id":agent_id,"display_name":row.display_name if row else agent_id,
        "framework":row.framework if row else None,"environment":row.environment if row else None,
        "owner":row.owner if row else None,"status":row.status if row else "observed-unregistered",
        "recent_events":[{"event_id":e.event_id,"event_type":e.event_type,"occurred_at":e.occurred_at,
            "run_id":e.run_id,"actor_id":e.actor_id,"resource_id":e.resource_id,
            "relationship_confidence":e.confidence} for e in events]}
