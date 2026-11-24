export type CaseItem = {id:string;title:string;severity:string;status:string;agent_ids?:string[];created_at?:string};
export type AgentItem = {agent_id:string;display_name:string;framework?:string|null;status:string;event_count:number;last_seen?:string|null};
export type EventItem = {event_id:string;event_type:string;occurred_at:string;agent_id?:string|null;run_id?:string|null;actor_id?:string|null;resource_id?:string|null;relationship_confidence:string};
export type EvidenceItem = {id:string;filename:string;sha256:string;byte_length:number;case_id?:string|null};
export type Snapshot = {cases:CaseItem[];agents:AgentItem[];events:EventItem[];evidence:EvidenceItem[]};

export async function apiRequest<T>(base:string,key:string,path:string,init:RequestInit={}):Promise<T>{
  const headers=new Headers(init.headers);
  headers.set("X-API-Key",key);
  if(init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type","application/json");
  const response=await fetch(base.replace(/\/$/,"")+path,{...init,headers});
  if(!response.ok){
    const body=await response.text();
    throw new Error(`API ${response.status}: ${body.slice(0,300)}`);
  }
  return response.json() as Promise<T>;
}

export async function loadSnapshot(base:string,key:string):Promise<Snapshot>{
  const [cases,agents,events,evidence]=await Promise.all([
    apiRequest<CaseItem[]>(base,key,"/v1/cases"),
    apiRequest<AgentItem[]>(base,key,"/v1/agents"),
    apiRequest<EventItem[]>(base,key,"/v1/events?limit=100"),
    apiRequest<EvidenceItem[]>(base,key,"/v1/evidence"),
  ]);
  return {cases,agents,events,evidence};
}
