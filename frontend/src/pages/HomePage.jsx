export default function HomePage({ onGitHub, onLocal }) {
  return (
    <main className="home">
      <div className="home-inner">
        <div className="wordmark">
          <span className="wordmark-slash">//</span>
          <span className="wordmark-name">CodeFlow</span>
        </div>
        <p className="wordmark-sub">Architecture diagrams from source code</p>
        <div className="home-actions">
          <button className="btn-primary" onClick={onGitHub}>
            Connect GitHub
          </button>
          <button className="btn-ghost" onClick={onLocal}>
            Generate from Output
          </button>
        </div>
      </div>
    </main>
  )
}