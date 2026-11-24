import React from "react";
import { Activity, ArrowRight, BadgeCheck, Building2, Cloud, Code2, Database, Fingerprint, FileCheck2, FileSearch, KeyRound, LockKeyhole, Network, Search, Shield, ShieldAlert, ShieldCheck, Workflow } from "lucide-react";

const demoEvents = [
  { time:"09:14:02.118", actor:"research-agent-07", action:"Agent run started", detail:"Run run_7f31 · Session sess_29a", kind:"observed", source:"Agent runtime trace" },
  { time:"09:14:03.402", actor:"svc-research-prod", action:"Credential referenced", detail:"Credential alias vault/research-reader", kind:"observed", source:"Identity audit record" },
  { time:"09:14:04.091", actor:"research-agent-07", action:"Document search invoked", detail:"Tool: knowledge.search · Scope: /quarterly/", kind:"observed", source:"Tool telemetry" },
  { time:"09:14:05.774", actor:"research-agent-07", action:"External destination referenced", detail:"Destination appears in tool output; delivery not independently confirmed", kind:"gap", source:"Tool telemetry" },
  { time:"09:14:07.010", actor:"case analyst", action:"Investigation opened", detail:"Case OC-DEMO-014 · Human review required", kind:"inference", source:"Case record" }
];

export function ForensicDemo(){
  const [selected,setSelected]=React.useState(0);
  const [showEvidence,setShowEvidence]=React.useState(true);
  const event=demoEvents[selected];
  return <div className="advanced-stack">
    <div className="preview-banner"><ShieldAlert size={17}/><span><b>Interactive demonstration</b><small>All names, timestamps and records below are synthetic training data. They are not live customer telemetry.</small></span><em>DEMO DATA</em></div>
    <div className="advanced-grid two">
      <article className="panel demo-summary"><div className="panelhead"><div><h2>OC-DEMO-014 · Suspected data exposure</h2><p>Illustrative investigation scenario</p></div><b className="demo-status">IN REVIEW</b></div><div className="demo-metrics"><div><small>RECORDS</small><b>05</b></div><div><small>IDENTITIES</small><b>02</b></div><div><small>OPEN GAPS</small><b>01</b></div></div><p className="demo-description">A research agent searched an internal knowledge area and later referenced an external destination. The available records do not independently prove that information was transmitted.</p><div className="demo-actions"><button className="primary" onClick={()=>setShowEvidence(v=>!v)}><FileSearch size={14}/>{showEvidence?"Hide evidence detail":"Show evidence detail"}</button><span>Human review required</span></div></article>
      <article className="panel"><div className="panelhead"><div><h2>Investigation assessment</h2><p>Separate observations from interpretation</p></div><BadgeCheck className="teal"/></div><div className="assessment-row"><i className="assessment-dot observed"/> <span><b>Verified observations</b><small>Agent run, credential reference and tool invocation appear in supplied records.</small></span></div><div className="assessment-row"><i className="assessment-dot inference"/> <span><b>Inference</b><small>The sequence may indicate a path to external disclosure; further corroboration is needed.</small></span></div><div className="assessment-row"><i className="assessment-dot gap"/> <span><b>Unknown</b><small>Whether data was actually delivered to the external destination.</small></span></div></article>
    </div>
    <article className="panel"><div className="panelhead"><div><h2>Cross-system event timeline</h2><p>Select a record to inspect its source and evidential meaning.</p></div><span className="demo-status">SYNTHETIC RECORDS</span></div><div className="demo-timeline">{demoEvents.map((item,i)=><button key={item.time} className={selected===i?"demo-event active":"demo-event"} onClick={()=>setSelected(i)}><time>{item.time}</time><i className={"assessment-dot "+item.kind}/><span><b>{item.action}</b><small>{item.actor} · {item.detail}</small></span><em>{item.kind==="observed"?"Observed":item.kind==="gap"?"Evidence gap":"Analyst action"}</em></button>)}</div>{showEvidence&&<div className="evidence-inspector"><div><small>SELECTED RECORD · {event.source}</small><h3>{event.action}</h3><p>{event.detail}</p></div><div className="inspector-meta"><span>Time <b>{event.time} UTC</b></span><span>Classification <b>{event.kind==="observed"?"Direct observation":event.kind==="gap"?"Evidence gap":"Analyst action"}</b></span><span>Source <b>{event.source}</b></span></div></div>}</article>
    <p className="advanced-note">This demonstration shows the intended investigation experience. It does not create a real case, connect to a source system or prove a real incident occurred.</p>
  </div>;
}

const integrations = [
  {name:"OpenTelemetry",type:"Agent & application telemetry",status:"Schema / ingestion foundation",icon:Activity,detail:"Structured telemetry ingestion is part of the current engineering foundation. Customer collector deployment and production coverage still require validation."},
  {name:"Amazon Web Services",type:"Cloud audit",status:"Adapter foundation",icon:Cloud,detail:"CloudTrail event adapter support exists in the codebase. Automated polling, durable checkpoints and backfill are not yet complete."},
  {name:"Microsoft Azure",type:"Cloud audit",status:"Push adapter implemented",icon:Cloud,detail:"Azure Activity Log records can be submitted through the API push endpoint. This is not a managed polling connector."},
  {name:"Google Cloud",type:"Cloud audit",status:"Push adapter implemented",icon:Cloud,detail:"Google Cloud Audit Log records can be submitted through the API push endpoint. This is not a managed polling connector."},
  {name:"GitHub",type:"Developer platform audit",status:"Push adapter implemented",icon:Code2,detail:"GitHub audit records can be submitted through the API push endpoint. Webhook lifecycle and historical backfill remain future work."},
  {name:"Identity providers",type:"Identity & access",status:"Roadmap",icon:Fingerprint,detail:"Planned support for identity context, delegated access and authentication events from enterprise identity providers."},
  {name:"SIEM & SOAR",type:"Security operations",status:"Roadmap",icon:Shield,detail:"Planned handoff of investigation context, evidence references and response workflow updates."},
  {name:"Databases & SaaS",type:"Business systems",status:"Roadmap",icon:Database,detail:"Connector priorities will be selected with design partners based on the systems involved in real investigations."}
];

export function IntegrationMarketplace(){
  const [filter,setFilter]=React.useState("All");
  const [query,setQuery]=React.useState("");
  const visible=integrations.filter(item=>(filter==="All"||item.type.includes(filter))&&(item.name+" "+item.detail).toLowerCase().includes(query.toLowerCase()));
  return <div className="advanced-stack">
    <div className="preview-banner"><Network size={17}/><span><b>Integration catalogue</b><small>Status describes the current codebase, not a claim that every connector is fully operational.</small></span><em>CONNECTOR READINESS</em></div>
    <div className="integration-tools"><div className="search-wrap"><Search size={15}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search integrations"/></div><div className="filter-pills">{["All","Cloud audit","Agent & application","Identity","Security operations"].map(f=><button key={f} className={filter===f?"active":""} onClick={()=>setFilter(f)}>{f}</button>)}</div></div>
    <div className="integration-grid">{visible.map(item=>{const Icon=item.icon;return <article className="panel integration-card" key={item.name}><div className="integration-card-top"><span className="integration-icon"><Icon size={19}/></span><em className={item.status.includes("implemented")?"status-ready":item.status==="Roadmap"?"status-roadmap":"status-foundation"}>{item.status}</em></div><h3>{item.name}</h3><small>{item.type}</small><p>{item.detail}</p><div className="integration-card-foot"><span>ORACLE CONTROL</span><span>Details <ArrowRight size={13}/></span></div></article>})}</div>
    <p className="advanced-note">A connector is not production-ready until authentication, permissions, retries, duplicate handling, checkpointing, backfill, monitoring and customer documentation have been tested.</p>
  </div>;
}

export function AdministrationCentre({apiUrl,apiKey}:{apiUrl:string;apiKey:string}){
  const [systemReadiness,setSystemReadiness]=React.useState<{status:string;checks:Record<string,string>;note?:string}|null>(null);
  const [readinessLoading,setReadinessLoading]=React.useState(false);
  const [readinessError,setReadinessError]=React.useState("");
  async function checkSystemReadiness(){
    setReadinessLoading(true);setReadinessError("");setSystemReadiness(null);
    try{
      const headers:Record<string,string>=apiKey.startsWith("eyJ")?{Authorization:`Bearer ${apiKey}`}:{"X-API-Key":apiKey};
      const response=await fetch(apiUrl.replace(/\/$/,"")+"/v1/admin/system/readiness",{headers});
      const result=await response.json();
      if(response.status===401)throw new Error("Sign in again to continue.");
      if(response.status===403)throw new Error("Your account needs the administrator role.");
      if(!response.ok&&response.status!==503)throw new Error(`Readiness check failed (HTTP ${response.status}).`);
      setSystemReadiness(result);
    }catch(error){setReadinessError(error instanceof Error?error.message:"Could not run system readiness check.");}
    finally{setReadinessLoading(false);}
  }
  const areas=[
    [Building2,"Organisation & workspace","Tenant profile, workspace ownership and environment settings.","Planned control surface"],
    [KeyRound,"Identity & access","SSO configuration, role mapping, session policy and service identities.","Backend foundation; UI preview"],
    [LockKeyhole,"Permissions & roles","Least-privilege access for investigators, administrators and auditors.","Requires end-to-end policy validation"],
    [FileCheck2,"Audit & retention","Administrative activity, evidence access, export history and retention rules.","Audit foundations exist; full policy UI pending"],
    [Database,"Data & storage","Storage region, evidence bucket, backup and export configuration.","Storage integration configured; recovery tests pending"],
    [Workflow,"Integrations & collectors","Approved source connections, collector status and ingestion health.","Connector operations roadmap"]
  ];
  return <div className="advanced-stack">
    <div className="preview-banner"><LockKeyhole size={17}/><span><b>Administration centre preview</b><small>These cards describe planned administration areas. They do not change tenant settings or grant access.</small></span><em>PREVIEW ONLY</em></div>
    <div className="integration-grid admin-grid">{areas.map(([Icon,title,desc,status])=>{const I=Icon as typeof Building2;return <article className="panel admin-card" key={title as string}><span className="integration-icon"><I size={20}/></span><h3>{title as string}</h3><p>{desc as string}</p><small>{status as string}</small></article>})}</div>
    <article className="panel"><div className="panelhead"><div><h2>Live system connection checks</h2><p>Administrator-only check of database and evidence-storage connectivity. No secrets are displayed.</p></div><button className="primary" onClick={checkSystemReadiness} disabled={readinessLoading||!apiKey}>{readinessLoading?"Checking…":"Run system check"}</button></div>
      {readinessError&&<p role="alert" className="advanced-note">{readinessError}</p>}
      {systemReadiness&&<><div className="readiness-item"><span>STATUS</span><b>{systemReadiness.status.toUpperCase()}</b><em>{systemReadiness.status==="ready"?"Connections available":"One or more checks need attention"}</em></div>{Object.entries(systemReadiness.checks).map(([name,status])=><div className="readiness-item" key={name}><span>{name.toUpperCase()}</span><b>{status.toUpperCase()}</b><em>{status==="ok"?"Connected":"Needs attention"}</em></div>)}{systemReadiness.note&&<p className="advanced-note">{systemReadiness.note}</p>}</>}
      {!systemReadiness&&!readinessError&&<p className="advanced-note">Run this check after signing in with an administrator account. It tests connectivity only; it is not a backup, retention or security certification.</p>}
    </article>
    <article className="panel"><div className="panelhead"><div><h2>Production readiness checklist</h2><p>Controls that must be verified before onboarding sensitive customer evidence.</p></div><ShieldCheck className="teal"/></div>{["Complete user sign-in and account recovery","Prove tenant isolation with automated negative tests","Validate role permissions for every sensitive endpoint","Configure retention, deletion and legal-hold procedures","Test backups and perform a successful restore","Review secrets, logs, dependency risks and incident response"].map((item,i)=><div className="readiness-item" key={item}><span>{String(i+1).padStart(2,"0")}</span><b>{item}</b><em>Not yet certified</em></div>)}</article>
  </div>;
}

export function TrustCentre(){
  const sections=[
    ["Security architecture","How identity, tenant boundaries, evidence storage and server-side secrets are intended to work.","Architecture overview"],
    ["Evidence integrity","What cryptographic digests establish, what they do not establish, and how custody records are used.","Evidence handling note"],
    ["Privacy & data handling","Data minimisation, retention, deletion, subprocessors and hosting-region information.","Policy work required"],
    ["Responsible AI","Human review, source-linked outputs, uncertainty labels and limits on automated conclusions.","AI use principles"],
    ["Deployment options","Managed cloud today; customer-controlled deployment is an engineering direction requiring validation.","Deployment guide"],
    ["Security contact","A route for responsible vulnerability reports and security questions.","Contact security team"]
  ];
  return <div className="advanced-stack">
    <div className="preview-banner"><ShieldCheck size={17}/><span><b>Trust centre</b><small>Transparency about implemented controls and remaining work. No certification or compliance claim is made here.</small></span><em>ENGINEERING PREVIEW</em></div>
    <div className="trust-intro"><h2>Trust is demonstrated, not declared.</h2><p>ORACLE CONTROL is being designed for sensitive investigations. The information below explains the principles and documentation customers should expect as the service matures.</p></div>
    <div className="integration-grid trust-grid">{sections.map(([title,desc,status],i)=><article className="panel trust-card" key={title}><span className="trust-number">0{i+1}</span><h3>{title}</h3><p>{desc}</p><small>{status}</small></article>)}</div>
    <div className="trust-disclaimer"><ShieldAlert size={17}/><p><b>Current disclosure</b><br/>The application is an engineering preview. It has not been represented as SOC 2 or ISO 27001 certified, and no independent certification is claimed. Production readiness requires completion and verification of authentication, access controls, recovery, privacy and security processes.</p></div>
  </div>;
}
