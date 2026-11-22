import React, { useCallback, useEffect, useState } from 'react';
import '../styles.css';

type Incident = { id: string; type: string; severity: string; status: string; title: string; description?: string; locationReference?: string; confidence: number; createdAt?: string; timestamp?: string; reviewerName?: string; };
const API = (((import.meta as any).env?.VITE_API_BASE_URL) || 'http://localhost:8000').replace(/\/$/, '');
const pretty = (value?: string) => value ? new Date(value).toLocaleString() : 'Time unavailable';

export const App: React.FC = () => {
  const [items, setItems] = useState<Incident[]>([]);
  const [filter, setFilter] = useState('all');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [report, setReport] = useState({ type: 'road_accident', title: '', description: '', locationReference: '' });

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/incidents?page_size=100`);
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const data = await res.json(); setItems(data.items || []); setMessage('');
    } catch (error) { setMessage(`Could not reach API: ${error instanceof Error ? error.message : 'unknown error'}`); }
  }, []);
  useEffect(() => { refresh(); const timer = window.setInterval(refresh, 15000); return () => clearInterval(timer); }, [refresh]);

  const act = async (id: string, action: string) => {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/incidents/${id}/${action}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ notes: action === 'confirm' ? 'Verified by operator' : 'Reviewed by operator' }) });
      if (!res.ok) { const body = await res.json().catch(() => ({})); throw new Error(body.detail || `Request failed (${res.status}); sign in through the API first if required.`); }
      await refresh(); setMessage(`Incident ${action === 'confirm' ? 'verified' : 'rejected'}.`);
    } catch (e) { setMessage(e instanceof Error ? e.message : 'Action failed'); } finally { setBusy(false); }
  };
  const submitReport = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true);
    try {
      const res = await fetch(`${API}/api/incidents/reports`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(report) });
      if (!res.ok) throw new Error(`Report submission failed (${res.status})`);
      setReport({type:'road_accident',title:'',description:'',locationReference:''}); await refresh(); setMessage('Community report submitted for operator review.');
    } catch(e) { setMessage(e instanceof Error ? e.message : 'Report failed'); } finally { setBusy(false); }
  };
  const visible = items.filter(i => filter === 'all' || i.status === filter);
  const pending = items.filter(i => ['detected','pending','inconclusive'].includes(i.status)).length;
  const active = items.filter(i => ['confirmed','dispatched','reviewing','in_progress'].includes(i.status)).length;
  return <main className="shell">
    <header className="topbar"><div className="brand"><span className="brand-icon">S</span><div><strong>SafeCity</strong><small>COMMUNITY RESPONSE NETWORK</small></div></div><div className="live"><i/> SYSTEM LIVE <button onClick={refresh}>Refresh</button></div></header>
    <section className="hero"><div><span className="eyebrow">INCIDENT OPERATIONS</span><h1>Good morning, Operator</h1><p>Review reports, verify detections, and coordinate a response.</p></div><div className="date">{new Date().toLocaleDateString(undefined,{weekday:'long',month:'long',day:'numeric'})}</div></section>
    <section className="stats"><article><span>NEEDS REVIEW</span><b>{pending}</b><small>Awaiting operator verification</small></article><article><span>ACTIVE RESPONSE</span><b>{active}</b><small>Verified incidents in progress</small></article><article><span>TOTAL REPORTS</span><b>{items.length}</b><small>All monitored incidents</small></article></section>
    {message && <div className="notice" role="status">{message}</div>}
    <div className="layout"><section className="panel incidents"><div className="panel-head"><div><span className="eyebrow">LIVE FEED</span><h2>Incident reports</h2></div><select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All statuses</option><option value="detected">Needs review</option><option value="confirmed">Verified</option><option value="rejected">Rejected</option><option value="resolved">Resolved</option></select></div>
      {visible.length === 0 ? <div className="empty"><span>✓</span><h3>All clear for now</h3><p>New camera detections and community reports will appear here.</p></div> : visible.map(i=><article className="incident" key={i.id}><div className="incident-top"><span className={`badge ${i.severity}`}>{i.severity}</span><span className="type">{i.type.replaceAll('_',' ')}</span><time>{pretty(i.createdAt || i.timestamp)}</time></div><h3>{i.title}</h3><p>{i.description || 'AI detection candidate. Verify before dispatch.'}</p><div className="meta">⌖ {i.locationReference || 'Location not provided'} <span>Confidence {Math.round((i.confidence || 0)*100)}%</span></div><div className="incident-bottom"><span className={`status ${i.status}`}>{i.status.replaceAll('_',' ')}</span>{['detected','pending','inconclusive'].includes(i.status) && <div><button disabled={busy} className="reject" onClick={()=>act(i.id,'reject')}>Reject</button><button disabled={busy} className="verify" onClick={()=>act(i.id,'confirm')}>Verify incident</button></div>}</div></article>)}</section>
      <aside className="panel report"><span className="eyebrow">COMMUNITY</span><h2>Submit a report</h2><p>Reports are reviewed by an operator before any response.</p><form onSubmit={submitReport}><label>Incident type<select value={report.type} onChange={e=>setReport({...report,type:e.target.value})}><option value="road_accident">Road accident</option><option value="fire">Fire</option><option value="smoke">Smoke</option><option value="other">Other concern</option></select></label><label>What happened?<input required maxLength={120} placeholder="Brief title" value={report.title} onChange={e=>setReport({...report,title:e.target.value})}/></label><label>Details<textarea rows={4} placeholder="Share what you observed" value={report.description} onChange={e=>setReport({...report,description:e.target.value})}/></label><label>Location<input placeholder="Address or landmark (optional)" value={report.locationReference} onChange={e=>setReport({...report,locationReference:e.target.value})}/></label><button className="verify submit" disabled={busy}>Send for review →</button></form><div className="privacy">Reports enter the review queue. No emergency services are contacted automatically.</div></aside></div>
    <footer>SafeCity <span>Incident coordination MVP · AI detections require human verification.</span></footer>
  </main>;
};
