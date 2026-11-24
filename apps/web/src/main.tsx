import React from "react";
import { createRoot } from "react-dom/client";
import { Activity, ShieldCheck, Database, Search, Network, FileSearch, ArrowUpRight, CircleDot, RefreshCw, PlugZap } from "lucide-react";
import { apiRequest, loadSnapshot, type Snapshot } from "./api";
import "./style.css";

function App(){
  const [page,setPage]=React.useState("Overview");
  const [apiUrl,setApiUrl]=React.useState("http://localhost:8000");
  const [apiKey,setApiKey]=React.useState("");
  const [snapshot,setSnapshot]=React.useState<Snapshot|null>(null);
  const [connection,setConnection]=React.useState<"disconnected"|"connecting"|"connected"|"error">("disconnected");
  const [error,setError]=React.useState("");
  const [caseTitle,setCaseTitle]=React.useState("");
  const [severity,setSeverity]=React.useState("medium");
  const [creating,setCreating]=React.useState(false);
  const nav:[string,React.ComponentType<{size?:number}>][]=[["Overview",Activity],["Investigations",FileSearch],["Agent activity",Network],["Evidence vault",Database],["Integrations",ShieldCheck],["Settings",CircleDot]];
  async function connect(){
    setConnection("connecting");setError("");
    try{const data=await loadSnapshot(apiUrl,apiKey);setSnapshot(data);setConnection("connected");}
    catch(e){setSnapshot(null);setConnection("error");setError(e instanceof Error?e.message:"Connection failed");}
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
  {cases.slice(0,8).map(c=><div className="case" key={c.id}><b className={"severity "+c.severity}>{c.severity.toUpperCase()}</b><div><strong>{c.title}</strong><small>{c.id} · {(c.agent_ids??[]).join(", ")||"No linked agents"}</small></div><em>{c.status}</em></div>)}
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
  {page==="Agent activity"&&<article className="panel detail-panel"><div className="panelhead"><div><h2>Agent event timeline</h2><p>Tenant-scoped events from the API</p></div></div>{events.map(e=><div className="event" key={e.event_id}><i className="eventdot"/><div><b>{e.event_type}</b><small>{e.agent_id||"Unattributed"} · run {e.run_id||"unknown"} · actor {e.actor_id||"unknown"} · {e.resource_id||"resource unknown"}</small></div><time>{new Date(e.occurred_at).toLocaleString()}</time><em>{e.relationship_confidence}</em></div>)}</article>}
  {page==="Evidence vault"&&<article className="panel detail-panel"><div className="panelhead"><div><h2>Evidence records</h2><p>Metadata only; use the API to upload, verify and export originals.</p></div></div>{evidence.map(e=><div className="event" key={e.id}><Database size={17}/><div><b>{e.filename}</b><small>{e.id} · {e.byte_length.toLocaleString()} bytes · case {e.case_id||"unassigned"}</small></div><code>{e.sha256.slice(0,16)}…</code></div>)}</article>}
  {page==="Integrations"&&<article className="panel detail-panel"><h2>Connector readiness</h2><p className="empty">OpenTelemetry and AWS CloudTrail record adapters are in the codebase. Live source authentication, polling, checkpointing and managed connector operations are not yet implemented. Other connector families are documented as roadmap items.</p></article>}
  {page==="Settings"&&<article className="panel detail-panel"><h2>Workspace connection</h2><p className="empty">API base URL and tenant key are held in this browser session only; they are not persisted by this console.</p></article>}
  <footer>ORACLE CONTROL <span>Evidence first. Conclusions with proof.</span><span>{connection==="connected"?"Live tenant data":"Not connected"}</span></footer></section></main></div>
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App/></React.StrictMode>);
