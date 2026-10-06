READ_HAPPY = r"""
() => {
  const pane = document.querySelector('.react-flow');
  const box = pane.getBoundingClientRect();
  const inside = r => r.left >= box.left && r.right <= box.right
    && r.top >= box.top && r.bottom <= box.bottom;
  const all = [...document.querySelectorAll('.react-flow__node')]
    .filter(n => !(n.getAttribute('data-id') || '').startsWith('box:'));
  const happy = all.filter(n => n.classList.contains('rf-happy')).map(n => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), onScreen: inside(r), height: Math.round(r.height) };
  });
  const edges = [...document.querySelectorAll('.react-flow__edge')].map(e => ({
    id: e.getAttribute('data-id') || e.id,
    marked: e.classList.contains('rf-happy') || e.getAttribute('data-happy') === 'true',
    width: parseFloat(getComputedStyle(e.querySelector('path') || e).strokeWidth) || 0,
  }));
  const widest = Math.max(0, ...edges.map(e => e.width));
  const narrowest = Math.min(...edges.map(e => e.width), widest);
  const marked = edges.some(e => e.marked);
  const happyEdges = edges.filter(e => marked ? e.marked : (widest > narrowest && e.width === widest));
  return { happy, happyEdges: happyEdges.map(e => e.id), edgesByClass: marked,
           other: all.length - happy.length };
}
"""

READ_CARDS = r"""
() => [...document.querySelectorAll('[data-testid^="contract-card-"]')].map((el, i) => ({
  index: i, testid: el.getAttribute('data-testid'), handler: el.getAttribute('data-handler'),
}))
"""
