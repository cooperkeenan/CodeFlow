READ_STATE = """
() => {
  const parse = (el) => {
    const m = /translate\\(([-0-9.]+)px,\\s*([-0-9.]+)px\\)/.exec(el.style.transform || '');
    const btn = el.querySelector('[role="button"]');
    return {
      id: el.getAttribute('data-id'),
      x: m ? Math.round(parseFloat(m[1])) : null,
      y: m ? Math.round(parseFloat(m[2])) : null,
      w: el.offsetWidth,
      h: el.offsetHeight,
      label: (el.innerText || '').trim().split('\\n')[0],
      toggle: btn ? btn.innerText.trim() : null,
    };
  };
  return {
    nodes: [...document.querySelectorAll('.react-flow__node')].map(parse),
    edges: document.querySelectorAll('.react-flow__edge').length,
    header: (document.querySelector('header')?.innerText || '').replace(/\\n/g, ' | '),
  };
}
"""


READ_ISOLATED = """
() => {
  const el = document.querySelector('.react-flow__node.rf-iso');
  if (!el) return { present: false };
  const canvas = document.querySelector('.react-flow');
  const shell = el.firstElementChild;
  const shellStyle = shell ? getComputedStyle(shell) : null;
  const box = el.getBoundingClientRect();
  const canvasBox = canvas ? canvas.getBoundingClientRect() : null;
  const w = Math.round(box.width), h = Math.round(box.height);
  const cw = canvasBox ? Math.round(canvasBox.width) : null;
  const ch = canvasBox ? Math.round(canvasBox.height) : null;
  return {
    present: true, id: el.getAttribute('data-id'), w, h, canvasW: cw, canvasH: ch,
    fillW: cw ? w / cw : null,
    fillH: ch ? h / ch : null,
    borderStyle: shellStyle ? shellStyle.borderStyle : null,
    borderWidth: shellStyle ? shellStyle.borderWidth : null,
    borderRadius: shellStyle ? shellStyle.borderRadius : null,
  };
}
"""

READ_DIMMED = """
() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const dim = nodes.filter(n => parseFloat(getComputedStyle(n).opacity) < 0.5);
  return { total: nodes.length, dimmed: dim.length,
           bright: nodes.filter(n => !dim.includes(n)).map(n => n.getAttribute('data-id')) };
}
"""


READ_FLOWCHART = """
() => {
  const root = document.querySelector('[data-testid="flowchart-view"]');
  if (!root) return { present: false, emptyText: '' };
  const nodeCount = parseInt(root.getAttribute('data-nodes') || '0', 10);
  const edgeCount = parseInt(root.getAttribute('data-edges') || '0', 10);
  if (nodeCount === 0) {
    return { present: false, emptyText: (root.innerText || '').trim() };
  }
  const shapes = [...root.querySelectorAll('svg rect, svg polygon')];
  const rootBox = root.getBoundingClientRect();
  const boxes = shapes.map((el, i) => {
    const b = el.getBoundingClientRect();
    return {
      id: String(i),
      x: Math.round(b.left - rootBox.left + root.scrollLeft),
      y: Math.round(b.top - rootBox.top + root.scrollTop),
      w: Math.round(b.width),
      h: Math.round(b.height),
    };
  });
  return {
    present: true,
    nodes: nodeCount,
    edges: edgeCount,
    boxes,
    scrollWidth: root.scrollWidth,
    clientWidth: root.clientWidth,
    scrollHeight: root.scrollHeight,
    clientHeight: root.clientHeight,
  };
}
"""
