export default function SettingsPage({ session }) {
  return (
    <section className="page-stack" aria-labelledby="settings-heading">
      <div className="page-heading"><div><span className="eyebrow">Settings</span><h1 id="settings-heading">Workspace security</h1><p>Current account and security posture. Configuration is managed server-side so sensitive values are never exposed to the browser.</p></div></div>
      <div className="settings-grid">
        <section className="panel" aria-labelledby="account-heading"><div className="section-title-row"><div><span className="eyebrow">Account</span><h2 id="account-heading">Identity</h2></div></div><dl className="settings-list"><div><dt>Email</dt><dd>{session.user.email}</dd></div><div><dt>User ID</dt><dd>{session.user.id}</dd></div><div><dt>Workspace</dt><dd>{session.workspace.name}</dd></div><div><dt>Role</dt><dd>{session.workspace.role}</dd></div></dl></section>
        <section className="panel" aria-labelledby="posture-heading"><div className="section-title-row"><div><span className="eyebrow">Security posture</span><h2 id="posture-heading">Application controls</h2></div></div><ul className="safe-list"><li>Session authentication uses an HTTP-only cookie; no browser API key is required.</li><li>Analysis requests are rate-limited per authenticated user.</li><li>HTML is analyzed structurally and never rendered as trusted DOM.</li><li>URLs are inspected structurally and are not automatically fetched.</li><li>Attachments are metadata-only and are never executed.</li><li>Analysis history is scoped to the authenticated workspace.</li></ul></section>
      </div>
    </section>
  )
}
