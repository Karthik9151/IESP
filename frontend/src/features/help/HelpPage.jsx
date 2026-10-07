const glossary=[['SVM margin','A ranking value showing how strongly the phishing model evidence leans in one direction. It is not a probability.'],['PKCE','Proof Key for Code Exchange: an OAuth safeguard that binds the authorization flow to the server-side exchange.'],['SSRF','Server-side request forgery: a risk where untrusted input can cause a server to reach private or internal network targets.'],['P1 / P2 / P3','IESP project proxy priority labels. They appear only after a NON-PHISHING verdict and are not human-annotated urgency ground truth.']]

export default function HelpPage({onStartTour}) {
  return <section className="page-stack" aria-labelledby="help-heading">
    <div className="page-heading">
      <div><span className="eyebrow">Operator guide</span><h1 id="help-heading">How IESP works</h1><p>A calm, inspectable pipeline for phishing defence and safe email triage.</p></div>
      <button className="button primary" onClick={onStartTour}>Replay first-run tour</button>
    </div>
    <section className="panel" aria-labelledby="pipeline-heading">
      <div className="section-title-row"><div><span className="eyebrow">Pipeline</span><h2 id="pipeline-heading">From message to decision</h2></div></div>
      <div className="help-pipeline">{['Email / Gmail / Microsoft','Safe parsing + normalization','Security feature extraction','TF-IDF + LinearSVC evidence','Security policy decision','Priority eligibility','P1 / P2 / P3'].map((step,index)=><div className="help-step" key={step}><span>{String(index+1).padStart(2,'0')}</span><strong>{step}</strong>{index<6&&<b>→</b>}</div>)}</div>
    </section>
    <div className="help-grid">
      <section className="panel">
        <div className="section-title-row"><div><span className="eyebrow">Verdict legend</span><h2>What each decision means</h2></div></div>
        <div className="legend-list large">
          {[['PHISHING','Do not interact. Strong phishing indicators.'],['SUSPICIOUS','Pause and review. Caution is warranted.'],['REVIEW REQUIRED','Evidence is incomplete or conflicting.'],['NON-PHISHING','No meaningful concern by the configured policy.']].map(([a,b])=><div className="legend-explain" key={a}><strong>{a}</strong><p>{b}</p></div>)}
        </div>
        <div className="withheld-box"><span>▣</span><div><strong>Priority is withheld for three verdicts.</strong><p>PHISHING, SUSPICIOUS and REVIEW REQUIRED never receive P1/P2/P3.</p></div></div>
      </section>
      <section className="panel">
        <div className="section-title-row"><div><span className="eyebrow">Glossary</span><h2>Technical terms</h2></div></div>
        <div className="faq-list">{glossary.map(([a,b])=><details key={a}><summary>{a}<span>+</span></summary><p>{b}</p></details>)}</div>
      </section>
    </div>
    <section className="panel">
      <div className="section-title-row"><div><span className="eyebrow">FAQ</span><h2>Common operator questions</h2></div></div>
      <div className="faq-list">
        <details><summary>Does IESP render email HTML?<span>+</span></summary><p>No. Email HTML is treated as untrusted data and is analyzed structurally rather than inserted into the DOM.</p></details>
        <details><summary>Can IESP automatically visit a URL?<span>+</span></summary><p>No. URLs are inspected structurally. Private/local destinations can be escalated as SSRF-sensitive.</p></details>
        <details><summary>Are Gmail and Microsoft connections write-enabled?<span>+</span></summary><p>No. The project is designed around read-only provider access and server-side token handling.</p></details>
        <details><summary>Why is the SVM margin not shown as a percentage?<span>+</span></summary><p>The LinearSVC decision function is a ranking margin, not a calibrated probability.</p></details>
        <details><summary>Are P1/P2/P3 real urgency labels?<span>+</span></summary><p>They are project proxy labels and only appear for NON-PHISHING messages.</p></details>
      </div>
    </section>
    <section className="panel limitations"><span className="eyebrow">Honest boundaries</span><h2>What this interface will never imply</h2><div className="limitation-grid"><div>✕ No fabricated accuracy or F1 scores</div><div>✕ No probability claims from SVM margins</div><div>✕ No automatic URL opening</div><div>✕ No executable attachment handling</div></div></section>
  </section>
}