import { useEffect, useState } from 'react';
import { getHealth } from './api';

type Connection = 'checking' | 'online' | 'offline';

function GhostMark() {
  return (
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path d="M7 26V14a9 9 0 0 1 18 0v12l-4-3-5 3-5-3-4 3Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <circle cx="12.5" cy="14" r="1.5" fill="currentColor" />
      <circle cx="19.5" cy="14" r="1.5" fill="currentColor" />
    </svg>
  );
}

export default function App() {
  const [connection, setConnection] = useState<Connection>('checking');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    let active = true;
    getHealth(controller.signal)
      .then(() => { if (active) setConnection('online'); })
      .catch(() => { if (active) setConnection('offline'); })
      .finally(() => window.clearTimeout(timeout));
    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [attempt]);

  function retry() {
    setConnection('checking');
    setAttempt((value) => value + 1);
  }

  return (
    <div className="shell">
      <aside className="sidebar" aria-label="Workspace navigation">
        <a className="brand" href="#workspace"><span className="brand-mark"><GhostMark /></span>GhostTab</a>
        <p className="sidebar-label">YOUR SPACE</p>
        <a className="nav-item selected" href="#workspace" aria-current="page"><span aria-hidden="true">▦</span> Workspaces</a>
        <a className="nav-item" href="#coming-next"><span aria-hidden="true">↗</span> What’s next</a>
        <div className="sidebar-footer"><span className="avatar">HG</span><div>Local workspace<small>Development · v0.1.0</small></div></div>
      </aside>
      <div className="main-column">
        <header className="topbar"><span>Workspace / <strong>Overview</strong></span><a href="https://github.com/Harsh-Gohel5/GhostTab" target="_blank" rel="noreferrer">View repository <span aria-hidden="true">↗</span></a></header>
        <main id="workspace">
          <div className="eyebrow"><span className="tiny-mark" /> A LITTLE LESS CONTEXT SWITCHING</div>
          <div className="page-heading"><div><h1>Your next task,<br /><span>already in context.</span></h1><p>The conversation, the code, and what changed.<br />One prepared workspace to pick up where work begins.</p></div><span className="stage-badge">Project foundation</span></div>

          <section className="workspace-card" aria-labelledby="empty-heading">
            <div className="empty-mark"><GhostMark /></div>
            <span className="card-eyebrow">A CLEAR PLACE TO START</span>
            <h2 id="empty-heading">Your first workspace belongs here.</h2>
            <p>Once GitHub is connected, you’ll be able to select an issue<br className="desktop-break" /> and bring its relevant context into one place.</p>
            <div className="connection-note"><span className="status-dot" /> No sources connected yet</div>
          </section>

          <section id="coming-next" aria-labelledby="next-heading">
            <div className="section-heading"><h2 id="next-heading">Building toward your first prepared task</h2><span>Coming next</span></div>
            <div className="feature-grid">
              <article><span className="step">01</span><h3>Connect the context</h3><p>Start with GitHub issues, documentation, and the commits that matter.</p></article>
              <article><span className="step">02</span><h3>Prepare the workspace</h3><p>A task brief, relevant files, and open questions grounded in source evidence.</p></article>
              <article><span className="step">03</span><h3>Keep it current</h3><p>Know when a source changes and your prepared context needs a refresh.</p></article>
            </div>
          </section>
          <footer className="workspace-footer">
            <div role="status" aria-live="polite" className={`api-status ${connection}`}><span className="status-dot" />{connection === 'online' ? 'Local API online' : connection === 'checking' ? 'Checking local API…' : 'Local API unavailable'}</div>
            {connection === 'offline' && <button className="retry" onClick={retry}>Retry connection</button>}
            <span className="footer-note">Built for the Meta Global AI Developer Hackathon</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
