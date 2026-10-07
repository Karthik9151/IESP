import { useEffect, useState } from 'react'
import { api } from '../../api'

const providers=[['gmail','Gmail'],['microsoft','Microsoft']]
export default function SettingsPage({session}){
 const [connections,setConnections]=useState([]); const [error,setError]=useState('')
 const load=()=>api.oauthConnections().then(setConnections).catch(e=>setError(e.message))
 useEffect(()=>{load(); const p=new URLSearchParams(window.location.search); if(p.get('oauth')){window.history.replaceState({},'',window.location.pathname);load()}},[])
 const connected=(name)=>connections.find(x=>x.provider===name)
 return <section className="page-stack" aria-labelledby="settings-heading">
  <div className="page-heading"><div><span className="eyebrow">Settings</span><h1 id="settings-heading">Workspace security</h1><p>Current account and provider security posture. Sensitive credentials remain server-side.</p></div></div>
  <div className="settings-grid">
   <section className="panel" aria-labelledby="account-heading"><div className="section-title-row"><div><span className="eyebrow">Account</span><h2 id="account-heading">Identity</h2></div></div><dl className="settings-list"><div><dt>Email</dt><dd>{session.user.email}</dd></div><div><dt>User ID</dt><dd>{session.user.id}</dd></div><div><dt>Workspace</dt><dd>{session.workspace.name}</dd></div><div><dt>Role</dt><dd>{session.workspace.role}</dd></div></dl></section>
   <section className="panel" aria-labelledby="providers-heading"><div className="section-title-row"><div><span className="eyebrow">Mail providers</span><h2 id="providers-heading">Read-only connections</h2></div></div>
    {error&&<div className="error" role="alert">{error}</div>}
    {providers.map(([id,label])=>{const item=connected(id);return <div key={id} className="provider-row"><div><strong>{label}</strong><div className="microcopy">{item?'Connected: '+(item.account_email||item.account_id):'Not connected'}</div></div>{item?<button className="button secondary" onClick={async()=>{await api.disconnectOAuth(id);load()}}>Disconnect</button>:<button className="button primary" onClick={()=>{window.location.href=(import.meta.env?.VITE_API_BASE_URL||'')+'/api/v1/oauth/'+id+'/start'}}>Connect</button>}</div>})}
    <p className="microcopy">IESP requests read-only mailbox access. Provider access/refresh tokens are never returned to browser JavaScript.</p>
   </section>
  </div>
  <section className="panel"><span className="eyebrow">Security posture</span><h2>Application controls</h2><ul className="safe-list"><li>Session authentication uses an HTTP-only cookie; no browser API key is required.</li><li>Provider OAuth uses state binding and PKCE.</li><li>Provider credentials are encrypted at rest on the server.</li><li>HTML is analyzed structurally and never rendered as trusted DOM.</li><li>URLs are inspected structurally and are not automatically fetched.</li><li>Attachments are metadata-only and are never executed.</li><li>Analysis history is scoped to the authenticated workspace.</li></ul></section>
 </section>
}