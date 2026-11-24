export type CaseItem = {id:string;title:string;severity:string;status:string;agent_ids?:string[];created_at?:string};
export type FindingItem = {id:string;title:string;statement:string;confidence:"directly_observed"|"correlated"|"inferred"|"unknown";evidence_ids:string[]};
export type CaseDetail = CaseItem & {description?:string;findings:FindingItem[]};
export type AgentItem = {agent_id:string;display_name:string;framework?:string|null;status:string;event_count:number;last_seen?:string|null};
export type EventItem = {event_id:string;event_type:string;occurred_at:string;agent_id?:string|null;run_id?:string|null;actor_id?:string|null;resource_id?:string|null;relationship_confidence:string};
export type EvidenceItem = {id:string;filename:string;sha256:string;byte_length:number;case_id?:string|null;verification_status?:"pending"|"verified"|"failed";verification_checked_at?:string|null};
export type AuthorityItem = {id:string;agent_id:string;principal_id:string;permission:string;resource_scope:string;decision:string;evidence_ids:string[]};
export type ApprovalItem = {id:string;agent_id:string;approver_id:string;action:string;decision:string};
export type LegalHoldItem = {id:string;case_id:string;evidence_id?:string|null;reason:string;status:string;placed_by:string;created_at:string};
export type RiskAgent = {agent_id:string;events_considered:number;max_event_score:number;triage_level:string;signals:{event_id:string;event_type:string;score:number;reasons:string[];confidence:string}[]};
export type Snapshot = {cases:CaseItem[];agents:AgentItem[];events:EventItem[];evidence:EvidenceItem[];authority:AuthorityItem[];approvals:ApprovalItem[];risk:RiskAgent[];legalHolds:LegalHoldItem[]};

export async function apiRequest<T>(base:string,key:string,path:string,init:RequestInit={}):Promise<T>{
  const headers=new Headers(init.headers);
  if(key.startsWith("eyJ")) headers.set("Authorization",`Bearer ${key}`);
  else headers.set("X-API-Key",key);
  if(init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type","application/json");
  const response=await fetch(base.replace(/\/$/,"")+path,{...init,headers});
  if(!response.ok){const body=await response.text();throw new Error(`API ${response.status}: ${body.slice(0,300)}`);}
  return response.json() as Promise<T>;
}

export async function loadSnapshot(base:string,key:string):Promise<Snapshot>{
  const [cases,agents,events,evidence,authority,approvals,riskResponse,legalHolds]=await Promise.all([
    apiRequest<CaseItem[]>(base,key,"/v1/cases"),
    apiRequest<AgentItem[]>(base,key,"/v1/agents"),
    apiRequest<EventItem[]>(base,key,"/v1/events?limit=100"),
    apiRequest<EvidenceItem[]>(base,key,"/v1/evidence"),
    apiRequest<AuthorityItem[]>(base,key,"/v1/authority/records"),
    apiRequest<ApprovalItem[]>(base,key,"/v1/authority/approvals"),
    apiRequest<{agents:RiskAgent[]}>(base,key,"/v1/intelligence/risk"),
    apiRequest<LegalHoldItem[]>(base,key,"/v1/legal-holds"),
  ]);
  return {cases,agents,events,evidence,authority,approvals,risk:riskResponse.agents,legalHolds};
}
