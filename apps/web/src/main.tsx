import React from "react";
import { createRoot } from "react-dom/client";
import { Activity, ShieldCheck, Database, Search, Network, FileSearch, ArrowUpRight, CircleDot, RefreshCw, PlugZap, BrainCircuit, Scale, FileCheck, LockKeyhole, type LucideIcon } from "lucide-react";
import { apiRequest, loadSnapshot, type Snapshot } from "./api";
import "./style.css";
import { CONTACT_EMAIL } from "./contact";
import { ForensicDemo, IntegrationMarketplace, AdministrationCentre, TrustCentre } from "./advanced";

function App(){
  const [page,setPage]=React.useState("Overview");
  const [apiUrl,setApiUrl]=React.useState("https://oracle-control-api-ok8v.onrender.com");
  const [apiKey,setApiKey]=React.useState("");
  const [snapshot,setSnapshot]=React.useState<Snapshot|null>(null);
  const [connection,setConnection]=React.useState<"disconnected"|"connecting"|"connected"|"error">("disconnected");
  const [error,setError]=React.useState("");
  const [caseTitle,setCaseTitle]=React.useState("");
  const [agentIdInput,setAgentIdInput]=React.useState("");
  const [agentNameInput,setAgentNameInput]=React.useState("");
  const [agentFrameworkInput,setAgentFrameworkInput]=React.useState("custom");
  const [severity,setSeverity]=React.useState("medium");
  const [creating,setCreating]=React.useState(false);
  const [selectedCase,setSelectedCase]=React.useState("");
  const [assistantResult,setAssistantResult]=React.useState("");
  const [authorityAgent,setAuthorityAgent]=React.useState("");
  const [principal,setPrincipal]=React.useState("");
  const [permission,setPermission]=React.useState("");
  const [resourceScope,setResourceScope]=React.useState("");
  const [approver,setApprover]=React.useState("");
  const [approvalAction,setApprovalAction]=React.useState("");
  const [verification,setVerification]=React.useState<Record<string,string>>({});
  const [holdReason,setHoldReason]=React.useState("");
  const [holdEvidenceId,setHoldEvidenceId]=React.useState("");
  const [custodyResult,setCustodyResult]=React.useState("");
  const [selectedFile,setSelectedFile]=React.useState<File|null>(null);
  const nav:[string,LucideIcon][]=[["Overview",Activity],["Investigations",FileSearch],["Agent activity",Network],["Authority",Scale],["Risk intelligence",BrainCircuit],["Legal holds",FileCheck],["Evidence vault",Database],["AI assistant",Search],["Integrations",ShieldCheck],["Settings",CircleDot],["Forensic demo",FileSearch],["Administration",ShieldCheck],["Trust centre",LockKeyhole]];
  async function connect(){
    setConnection("connecting");setError("");
    try{const data=await loadSnapshot(apiUrl,apiKey);setSnapshot(data);setConnection("connected");if(!selectedCase&&data.cases.length)setSelectedCase(data.cases[0].id);}
    catch(e){setSnapshot(null);setConnection("error");setError(e instanceof Error?e.message:"Connection failed");}
  }
  async function registerAgent(event:React.FormEvent){
    event.preventDefault();
    try{await apiRequest(apiUrl,apiKey,"/v1/agents",{method:"POST",body:JSON.stringify({agent_id:agentIdInput,display_name:agentNameInput,framework:agentFrameworkInput})});setAgentIdInput("");setAgentNameInput("");await connect();}
    catch(e){setError(e instanceof Error?e.message:"Agent registration failed");}
  }
  async function exportCase(id:string){
    try{
      const response=await fetch(apiUrl.replace(/\/$/,"")+ `/v1/cases/${id}/export`,{headers:{"X-API-Key":apiKey}});
      if(!response.ok)throw new Error(`Export failed: ${response.status}`);
      const blob=await response.blob();const url=URL.createObjectURL(blob);
      const anchor=document.createElement("a");anchor.href=url;anchor.download=`oracle-control-${id}.zip`;anchor.click();URL.revokeObjectURL(url);
      await connect();
    }catch(e){setError(e instanceof Error?e.message:"Case export failed");}
  }
  async function updateCaseStatus(id:string,status:string){
    try{await apiRequest(apiUrl,apiKey,`/v1/cases/${id}/status?status=${encodeURIComponent(status)}`,{method:"PATCH"});await connect();}
    catch(e){setError(e instanceof Error?e.message:"Case status update failed");}
  }
  async function createCase(event:React.FormEvent){
    event.preventDefault();if(!caseTitle.trim()||!apiKey)return;
    setCreating(true);setError("");
    try{await apiRequest(apiUrl,apiKey,"/v1/cases",{method:"POST",body:JSON.stringify({title:caseTitle,severity})});setCaseTitle("");await connect();}
    catch(e){setError(e instanceof Error?e.message:"Could not create case");}
    finally{setCreating(false);}
  }
  const cases=snapshot?.cases??[];
  const events=snapshot?.events??[];
  const agents=snapshot?.agents??[];
  const evidence=snapshot?.evidence??[];
  const authority=snapshot?.authority??[];
  const approvals=snapshot?.approvals??[];
  const risks=snapshot?.risk??[];
  const legalHolds=snapshot?.legalHolds??[];
  async function recordAuthority(event:React.FormEvent){
    event.preventDefault();
    try{await apiRequest(apiUrl,apiKey,"/v1/authority/records",{method:"POST",body:JSON.stringify({agent_id:authorityAgent,principal_id:principal,permission,resource_scope:resourceScope,decision:"granted",source_system:"analyst-recorded"})});setPrincipal("");setPermission("");setResourceScope("");await connect();}
    catch(e){setError(e instanceof Error?e.message:"Could not record authority");}
  }
  async function recordApproval(event:React.FormEvent){
    event.preventDefault();
    try{await apiRequest(apiUrl,apiKey,"/v1/authority/approvals",{method:"POST",body:JSON.stringify({agent_id:authorityAgent,approver_id:approver,action:approvalAction,resource_scope:resourceScope,decision:"approved",source_system:"analyst-recorded"})});setApprover("");setApprovalAction("");await connect();}
    catch(e){setError(e instanceof Error?e.message:"Could not record approval");}
  }
  async function verifyEvidence(id:string){
    try{const result=await apiRequest<{valid:boolean}>(apiUrl,apiKey,`/v1/evidence/${id}/verify`,{method:"POST"});setVerification(prev=>({...prev,[id]:result.valid?"Verified":"Integrity failure"}));await connect();}
    catch(e){setError(e instanceof Error?e.message:"Evidence verification failed");}
  }
  async function uploadEvidence(event:React.FormEvent){
    event.preventDefault();if(!selectedFile)return;
    const form=new FormData();form.append("file",selectedFile);form.append("source_system","analyst-upload");
    if(selectedCase)form.append("case_id",selectedCase);
    try{await apiRequest(apiUrl,apiKey,"/v1/evidence",{method:"POST",body:form});setSelectedFile(null);await connect();}
    catch(e){setError(e instanceof Error?e.message:"Evidence upload failed");}
  }
  async function createLegalHold(event:React.FormEvent){
    event.preventDefault();if(!selectedCase||!holdReason.trim())return;
    try{await apiRequest(apiUrl,apiKey,"/v1/legal-holds",{method:"POST",body:JSON.stringify({case_id:selectedCase,evidence_id:holdEvidenceId||null,reason:holdReason})});setHoldReason("");setHoldEvidenceId("");await connect();}
    catch(e){setError(e instanceof Error?e.message:"Could not place legal hold");}
  }
  async function releaseLegalHold(id:string){
    try{await apiRequest(apiUrl,apiKey,`/v1/legal-holds/${id}/release`,{method:"POST"});await connect();}
    catch(e){setError(e instanceof Error?e.message:"Could not release legal hold");}
  }
  async function loadCustody(id:string){
    try{const chain=await apiRequest<unknown[]>(apiUrl,apiKey,`/v1/custody/evidence/${id}`);setCustodyResult(JSON.stringify(chain,null,2));}
    catch(e){setError(e instanceof Error?e.message:"Could not load custody history");}
  }
  async function draftAssistant(){
    if(!selectedCase)return;
    try{const result=await apiRequest<unknown>(apiUrl,apiKey,`/v1/assistant/cases/${selectedCase}/draft`,{method:"POST",body:JSON.stringify({include_event_payloads:false})});setAssistantResult(JSON.stringify(result,null,2));}
    catch(e){setError(e instanceof Error?e.message:"Assistant request failed");}
  }
  const caseSelect=<select value={selectedCase} onChange={e=>setSelectedCase(e.target.value)} aria-label="Select case">{cases.map(item=><option key={item.id} value={item.id}>{item.title}</option>)}</select>;
  const activeCases=cases.filter(c=>!["resolved","closed"].includes(c.status)).length;
  const metrics=[
    ["ACTIVE INVESTIGATIONS",snapshot?String(activeCases).padStart(2,"0"):"—",snapshot?"Live case records":"Connect API to load",FileSearch],
    ["AGENTS OBSERVED",snapshot?String(agents.length):"—",snapshot?"Registered and observed":"Connect API to load",Network],
    ["EVENTS INGESTED",snapshot?events.length.toLocaleString():"—",snapshot?"Latest 100 event records":"Connect API to load",Activity],
    ["EVIDENCE RECORDS",snapshot?evidence.length.toLocaleString():"—",snapshot?"Stored evidence metadata":"Connect API to load",ShieldCheck],
  ] as const;
  return <div className="layout"><aside><div className="brand"><span>O</span><div><b>ORACLE</b><small>CONTROL</small></div></div><div className="workspace"><i/> CUSTOMER WORKSPACE <span>⌄</span></div><label>OPERATIONS</label>{nav.map(([name,Icon])=><button key={name} className={page===name?"nav selected":"nav"} onClick={()=>setPage(name)}><Icon size={17}/>{name}</button>)}<div className="sidefoot"><ShieldCheck size={16}/> Evidence integrity controls<small>ENGINEERING PREVIEW</small></div></aside>
  <main><header><div><span>Workspace</span> / <b>{page}</b></div><div className="sys"><i className={connection==="connected"?"":"off"}/>{connection==="connected"?"API CONNECTED":"API NOT CONNECTED"}<span className="avatar">OC</span></div></header>
  <section className="content"><div className="eyebrow">AI INCIDENT INVESTIGATION PLATFORM</div><div className="title"><div><h1>{page==="Overview"?"Command centre":page}</h1><p>Independent visibility into agent actions, authority and evidence.</p></div><button className="primary" onClick={connect} disabled={connection==="connecting"}><RefreshCw size={15}/> {connection==="connecting"?"Connecting…":"Refresh workspace"}</button></div>
  <div className="connection"><div className="connection-title"><PlugZap size={18}/><div><b>Connect your ORACLE CONTROL API</b><small>Live dashboard data is loaded from your tenant API. No sample metrics are shown.</small></div></div><div className="connection-fields"><input aria-label="API base URL" value={apiUrl} onChange={e=>setApiUrl(e.target.value)} placeholder="http://localhost:8000"/><input aria-label="API key" type="password" value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="Tenant API key"/><button onClick={connect} disabled={!apiKey||connection==="connecting"}>Connect</button></div>{error&&<p className="error">{error}</p>}{connection==="connected"&&<p className="success">Connected. Dashboard figures below are live API results.</p>}</div>
  <div className="principle"><ShieldCheck size={18}/><span><b>Forensic principle</b> — findings distinguish direct observations, correlations, inferences and unknowns. A digest does not prove source authenticity or collection completeness.</span></div>
  <div className="metrics">{metrics.map(([label,value,sub,Icon])=><article className="metric" key={label}><div>{label}<Icon size={17}/></div><strong>{value}</strong><small>{sub}</small></article>)}</div>
  {page==="Overview"||page==="Investigations"?<div className="panels"><article className="panel cases"><div className="panelhead"><div><h2>Investigation queue</h2><p>Live tenant cases</p></div><button onClick={()=>setPage("Investigations")}>View all <ArrowUpRight size={14}/></button></div>
  {snapshot&&cases.length===0&&<p className="empty">No investigation cases have been created in this tenant.</p>}
  {cases.slice(0,8).map(c=><div className="case" key={c.id}><b className={"severity "+c.severity}>{c.severity.toUpperCase()}</b><div><strong>{c.title}</strong><small>{c.id} · {(c.agent_ids??[]).join(", ")||"No linked agents"}</small></div><button className="text-btn" onClick={()=>exportCase(c.id)}>Export</button><select className="status-select" value={c.status} onChange={e=>updateCaseStatus(c.id,e.target.value)}><option value="open">Open</option><option value="investigating">Investigating</option><option value="contained">Contained</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select></div>)}
  {!snapshot&&<p className="empty">Connect the API to load real investigations.</p>}
  <form className="create-case" onSubmit={createCase}><input value={caseTitle} onChange={e=>setCaseTitle(e.target.value)} placeholder="New investigation title" aria-label="New investigation title"/><select value={severity} onChange={e=>setSeverity(e.target.value)} aria-label="Severity"><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select><button disabled={!snapshot||!caseTitle.trim()||creating}>{creating?"Creating…":"Create case"}</button></form></article>
  <article className="panel"><div className="panelhead"><div><h2>Evidence vault</h2><p>Stored evidence records</p></div><ShieldCheck className="teal"/></div><div className="health">{snapshot?evidence.length:"—"}</div><strong className="healthlabel">Evidence items indexed</strong><small>Integrity must be verified per evidence item.</small><div className="legend"><span>Evidence records <b>{snapshot?evidence.length:"—"}</b></span><span>Verified <b>Not aggregated</b></span></div></article>
  <article className="panel"><div className="panelhead"><div><h2>Recent agent activity</h2><p>Latest ingested events</p></div><button onClick={()=>setPage("Agent activity")}>Explore <ArrowUpRight size={14}/></button></div>
  {events.slice(0,6).map((e,i)=><div className="event" key={e.event_id}><i className={"eventdot e"+(i%3)}/><div><b>{e.event_type}</b><small>{e.agent_id||"Unattributed"} · {e.resource_id||"Resource not recorded"}</small></div><time>{new Date(e.occurred_at).toLocaleTimeString()}</time><em>{e.relationship_confidence.replace("_"," ")}</em></div>)}
  {snapshot&&events.length===0&&<p className="empty">No event records found.</p>}{!snapshot&&<p className="empty">Connect the API to load activity.</p>}</article>
  <article className="panel"><div className="panelhead"><div><h2>Agent inventory</h2><p>Registered and observed identities</p></div></div>
  {agents.slice(0,6).map(a=><div className="connector" key={a.agent_id}><span>AI</span><div><b>{a.display_name}</b><small>{a.agent_id} · {a.framework||"Framework not declared"}</small></div><em>{a.status}</em></div>)}
  {snapshot&&agents.length===0&&<p className="empty">No agent identities registered or observed.</p>}
  {!snapshot&&<p className="empty">Connect the API to load agents.</p>}</article></div>:null}
  {page==="Agent activity"&&<><article className="panel detail-panel"><div className="panelhead"><div><h2>Register agent identity</h2><p>Explicit agent identifiers support reliable investigation correlation.</p></div></div><form className="create-case" onSubmit={registerAgent}><input value={agentIdInput} onChange={e=>setAgentIdInput(e.target.value)} placeholder="Stable agent ID" required/><input value={agentNameInput} onChange={e=>setAgentNameInput(e.target.value)} placeholder="Display name" required/><input value={agentFrameworkInput} onChange={e=>setAgentFrameworkInput(e.target.value)} placeholder="Framework"/><button disabled={!snapshot}>Register agent</button></form>{agents.map(a=><div className="connector" key={a.agent_id}><span>AI</span><div><b>{a.display_name}</b><small>{a.agent_id} · {a.framework||"Framework unknown"} · {a.event_count} events</small></div><em>{a.status}</em></div>)}</article><article className="panel detail-panel"><div className="panelhead"><div><h2>Agent event timeline</h2><p>Tenant-scoped events from the API</p></div></div>{events.map(e=><div className="event" key={e.event_id}><i className="eventdot"/><div><b>{e.event_type}</b><small>{e.agent_id||"Unattributed"} · run {e.run_id||"unknown"} · actor {e.actor_id||"unknown"} · {e.resource_id||"resource unknown"}</small></div><time>{new Date(e.occurred_at).toLocaleString()}</time><em>{e.relationship_confidence}</em></div>)}</article></>}
  {page==="Authority"&&<article className="panel detail-panel"><div className="panelhead"><div><h2>Authority and approval history</h2><p>Record and review permissions, scopes and human approvals.</p></div></div><form className="create-case" onSubmit={recordAuthority}><input value={authorityAgent} onChange={e=>setAuthorityAgent(e.target.value)} placeholder="Agent ID" required/><input value={principal} onChange={e=>setPrincipal(e.target.value)} placeholder="Principal identity" required/><input value={permission} onChange={e=>setPermission(e.target.value)} placeholder="Permission" required/><input value={resourceScope} onChange={e=>setResourceScope(e.target.value)} placeholder="Resource scope" required/><button disabled={!snapshot}>Record grant</button></form><h3>Authority records</h3>{authority.map(a=><div className="event" key={a.id}><Scale size={16}/><div><b>{a.agent_id} · {a.permission}</b><small>{a.principal_id} → {a.resource_scope}</small></div><em>{a.decision}</em></div>)}<h3>Record human approval</h3><form className="create-case" onSubmit={recordApproval}><input value={authorityAgent} onChange={e=>setAuthorityAgent(e.target.value)} placeholder="Agent ID" required/><input value={approver} onChange={e=>setApprover(e.target.value)} placeholder="Approver identity" required/><input value={approvalAction} onChange={e=>setApprovalAction(e.target.value)} placeholder="Approved action" required/><button disabled={!snapshot}>Record approval</button></form><h3>Human approvals</h3>{approvals.map(a=><div className="event" key={a.id}><ShieldCheck size={16}/><div><b>{a.agent_id} · {a.action}</b><small>Approver: {a.approver_id}</small></div><em>{a.decision}</em></div>)}</article>}
  {page==="Risk intelligence"&&<article className="panel detail-panel"><div className="panelhead"><div><h2>Explainable risk triage</h2><p>Rule-based indicators, not calibrated probabilities or proof of malicious activity.</p></div></div>{risks.map(r=><div className="risk-row" key={r.agent_id}><b>{r.agent_id}</b><small>{r.events_considered} events · max signal {r.max_event_score}/100 · {r.triage_level}</small>{r.signals.map(s=><p key={s.event_id}>{s.event_type} · {s.score}/100 · {s.reasons.join("; ")}</p>)}</div>)}{custodyResult&&<pre className="assistant-output">{custodyResult}</pre>}</article>}
  {page==="Legal holds"&&<article className="panel detail-panel"><div className="panelhead"><div><h2>Legal hold register</h2><p>Record and release preservation instructions for cases and evidence.</p></div></div><form className="create-case" onSubmit={createLegalHold}>{caseSelect}<select value={holdEvidenceId} onChange={e=>setHoldEvidenceId(e.target.value)}><option value="">Entire case</option>{evidence.map(item=><option key={item.id} value={item.id}>{item.filename}</option>)}</select><input value={holdReason} onChange={e=>setHoldReason(e.target.value)} placeholder="Reason for preservation" required/><button disabled={!snapshot||!holdReason.trim()}>Place hold</button></form>{legalHolds.map(h=><div className="event" key={h.id}><FileCheck size={16}/><div><b>{h.reason}</b><small>{h.case_id} · {h.evidence_id||"Entire case"} · placed by {h.placed_by}</small></div><em>{h.status}</em>{h.status==="active"&&<button className="text-btn" onClick={()=>releaseLegalHold(h.id)}>Release</button>}</div>)}</article>}
  {page==="AI assistant"&&<article className="panel detail-panel"><div className="panelhead"><div><h2>Evidence-grounded investigation assistant</h2><p>Provider disabled by default. Without a configured model, this returns structured case context only.</p></div></div><div className="create-case">{caseSelect}<button onClick={draftAssistant} disabled={!snapshot||!selectedCase}>Prepare case draft</button></div>{assistantResult&&<pre className="assistant-output">{assistantResult}</pre>}</article>}
  {page==="Evidence vault"&&<article className="panel detail-panel"><div className="panelhead"><div><h2>Evidence collection</h2><p>Upload originals, preserve digest and attach them to an investigation.</p></div></div><form className="create-case" onSubmit={uploadEvidence}>{caseSelect}<input type="file" onChange={e=>setSelectedFile(e.target.files?.[0]??null)} required/><button disabled={!snapshot||!selectedFile}>Upload evidence</button></form>{evidence.map(e=><div className="event" key={e.id}><Database size={17}/><div><b>{e.filename}</b><small>{e.id} · {e.byte_length.toLocaleString()} bytes · case {e.case_id||"unassigned"}</small></div><code>{e.sha256.slice(0,16)}…</code><button className="text-btn" onClick={()=>verifyEvidence(e.id)}>Verify</button><button className="text-btn" onClick={()=>loadCustody(e.id)}>Custody</button><em>{verification[e.id]||"Not checked"}</em></div>)}{custodyResult&&<pre className="assistant-output">{custodyResult}</pre>}</article>}
  {page==="Integrations"&&<IntegrationMarketplace/>}{page==="Forensic demo"&&<ForensicDemo/>}{page==="Administration"&&<AdministrationCentre/>}{page==="Trust centre"&&<TrustCentre/>}
  {page==="Settings"&&<article className="panel detail-panel"><h2>Workspace connection</h2><p className="empty">API base URL and tenant key are held in this browser session only; they are not persisted by this console.</p></article>}
  <footer>ORACLE CONTROL <span>Evidence first. Conclusions with proof.</span><span>{connection==="connected"?"Live tenant data":"Not connected"}</span><a href={`mailto:${CONTACT_EMAIL}`}>Business & partnerships: {CONTACT_EMAIL}</a></footer></section></main></div>
}
if (window.location.pathname === "/app" || window.location.pathname.startsWith("/app/")) {
  createRoot(document.getElementById("root")!).render(<React.StrictMode><App/></React.StrictMode>);
} else {
  import("./marketing").then(({ default: MarketingPage }) => {
    createRoot(document.getElementById("root")!).render(<React.StrictMode><MarketingPage/></React.StrictMode>);
  });
}
