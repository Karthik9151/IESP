import { useEffect, useState } from 'react'
import { api } from '../../api'

const providers=[['gmail','Gmail'],['microsoft','Microsoft']]
export default function SettingsPage({session,onToast}) {
 const [connections,setConnections]=useState([]); const [providerMessages,setProviderMessages]=useState({}); const [error,setError]=useState(''); const [loadingProvider,setLoadingProvider]=useState('')
 const load=()=>api.oauthConnections().then(setConnections).catch(e=>setError(e.message))
 useEffect(()=>{load(); const p=new URLSearchParams(window.location.search); if(p.get('oauth')){window.history.replaceState({},'',window.location.pathname);load()}},[])
 const connected=(name)=>connections.find(x=>x.provider===name)
 const loadMessages=async(id)=>{
   setLoadingProvider(id); setError('')
   try{const data=await api.listProviderMessages(id);setProviderMessages(v=>({...v,[id]:data.items||data}))}catch(e){setError(e.message)}finally{setLoadingProvider('')}
 }
 const disconnect=async(id,label)=>{
   if(!window.confirm('Disconnect '+label+'? IESP will remove the stored provider connection.')) return
   try{await api.disconnectOAuth(id); await load(); onToast?.({type:'success',message:label+' mailbox disconnected.'})}catch(e){setError(e.message)}
 }
 return <section className="page-stack" aria-labelledby="settings-heading">
  <div className="page-heading"><div><span className="eyebrow">Control plane</span><h1 id="settings-heading">Workspace settings</h1><p>Manage identity and read-only mailbox connections. Provider secrets remain outside browser JavaScript.</p></div></div>
  <div className="settings-grid">
   <section className="panel" aria-labelledby="account-heading"><div className="section-title-row"><div><span className="eyebrow">Identity</span><h2 id="account-heading">Profile &amp; session</h2></div></div><dl className="metadata-list"><div><dt>Email</dt><dd>{session.user.email}</dd></div><div><dt>User ID</dt><dd className="mono-text">{session.user.id}</dd></div><div><dt>Workspace</dt><dd>{session.workspace.name}</dd></div><div><dt>Role</dt><dd>{session.workspace.role}</dd></div><div><dt>Session</dt><dd><span className="safe-badge">HTTP-ONLY COOKIE</span></dd></div></dl></section>
   <section className="panel" aria-labelledby="providers-heading"><div className="section-title-row"><div><span className="eyebrow">Mailbox access</span><h2 id="providers-heading">Connected mailboxes</h2></div></div>
    {error&&<div className="error" role="alert">{error}</div>}
    {providers.map(([id,label])=>{const item=connected(id);return <article key={id} className="provider-card"><div className="provider-card-head"><div><div className="provider-logo" aria-hidden="true">{id==='gmail'?'G':'M'}</div><div><strong>{label}</strong><small>{item?'Connected'+(item.account_email?' · '+item.account_email:''):'Not connected'}</small></div></div><span className={'connection-status '+(item?'connected':'not-connected')}>{item?'Connected':'Not connected'}</span></div><div className="provider-badges"><span className="safe-badge">READ-ONLY ACCESS</span><span className="microcopy">Tokens encrypted server-side</span></div><div className="button-row">{item?<><button className="button secondary" onClick={()=>loadMessages(id)} disabled={loadingProvider===id}>{loadingProvider===id?'Loading…':'View messages'}</button><button className="button danger" onClick={()=>disconnect(id,label)}>Disconnect</button></>:<a className="button primary" href={(import.meta.env?.VITE_API_BASE_URL||'')+'/api/v1/oauth/'+id+'/start'}>Connect read-only</a>}</div>{providerMessages[id]&&<div className="provider-messages">{providerMessages[id].length?providerMessages[id].slice(0,8).map((m,index)=><div className="provider-message" key={m.id||m.message_id||index}><div><strong>{m.subject||'(no subject)'}</strong><small>{m.from||m.sender||m.account_email||'Mailbox message'}</small></div><button className="button subtle compact-button" onClick={async()=>{try{await api.analyzeProviderMessage(id,m.id||m.message_id);onToast?.({type:'success',message:'Provider message sent for analysis.'})}catch(e){setError(e.message)}}}>Analyze</button></div>):<span className="microcopy">No provider messages returned.</span>}</div>}</article>})}
    <p className="microcopy">IESP requests read-only mailbox access. Provider access/refresh tokens are never returned to browser JavaScript.</p>
   </section>
  </div>
  <section className="panel" aria-labelledby="posture-heading"><div className="section-title-row"><div><span className="eyebrow">Security posture</span><h2 id="posture-heading">Application controls</h2></div></div><div className="control-grid">{[['Session','HTTP-only cookie; no browser API key'],['OAuth','State binding + PKCE'],['Content','HTML never rendered; URLs are not auto-visited'],['Attachments','Metadata only; never executed'],['Data scope','History scoped to authenticated workspace'],['Priority','Hidden until NON-PHISHING']].map(([a,b])=><div key={a}><span>{a}</span><strong>{b}</strong></div>)}</div></section>
 </section>
}
