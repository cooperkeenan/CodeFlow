READ_HAPPY = r"""
() => {
  const pane = document.querySelector('.react-flow');
  const box = pane.getBoundingClientRect();
  const inside = r => r.left >= box.left && r.right <= box.right
    && r.top >= box.top && r.bottom <= box.bottom;
  const host = document.querySelector('[data-testid="endpoint-diagram"]');
  const parse = name => { try { return JSON.parse(host.getAttribute(name) || '[]'); } catch (e) { return []; } };
  const expected = host ? parse('data-happy-ids') : [];
  const expectedEdges = host ? parse('data-happy-edges') : [];
  const all = [...document.querySelectorAll('.react-flow__node')]
    .filter(n => !(n.getAttribute('data-id') || '').startsWith('box:'));
  const byId = new Map(all.map(n => [n.getAttribute('data-id'), n]));
  const happy = all.filter(n => n.classList.contains('rf-happy')).map(n => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), onScreen: inside(r), height: Math.round(r.height) };
  });
  const lit = new Set(happy.map(n => n.id));
  const edges = [...document.querySelectorAll('.react-flow__edge')].map(e => ({
    id: e.getAttribute('data-id') || e.id,
    marked: e.classList.contains('rf-happy') || e.getAttribute('data-happy') === 'true',
    width: parseFloat(getComputedStyle(e.querySelector('path') || e).strokeWidth) || 0,
  }));
  const widest = Math.max(0, ...edges.map(e => e.width));
  const narrowest = Math.min(...edges.map(e => e.width), widest);
  const marked = edges.some(e => e.marked);
  const happyEdges = edges.filter(e => marked ? e.marked : (widest > narrowest && e.width === widest));
  return {
    hasHost: !!host, expected, expectedEdges, happy,
    missing: expected.filter(id => !byId.has(id)),
    unhighlighted: expected.filter(id => byId.has(id) && !lit.has(id)),
    offScreen: happy.filter(n => !n.onScreen).map(n => n.id),
    happyEdges: happyEdges.map(e => e.id), edgesByClass: marked,
    other: all.length - happy.length,
  };
}
"""

READ_SETTLED = r"""
() => JSON.stringify([...document.querySelectorAll('.react-flow__node')].map(n =>
  [n.getAttribute('data-id'), n.style.transform, n.className.includes('rf-happy'),
   Math.round(n.getBoundingClientRect().x), Math.round(n.getBoundingClientRect().y)]))
  + document.querySelectorAll('.react-flow__edge').length
"""

READ_CARDS = r"""
() => [...document.querySelectorAll('[data-testid^="contract-card-"]')].map((el, i) => ({
  index: i, testid: el.getAttribute('data-testid'), handler: el.getAttribute('data-handler'),
}))
"""
