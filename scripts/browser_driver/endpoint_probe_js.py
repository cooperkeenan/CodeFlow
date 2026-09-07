READ_ENDPOINT_DETAIL = r"""
() => {
  const page = document.querySelector('[data-testid="endpoint-page"]');
  if (!page) return { present: false };
  const header = page.querySelector('header');
  const chip = header ? header.querySelector('.MuiChip-label') : null;
  const headerTexts = header ? [...header.querySelectorAll('p')].map(p => p.textContent.trim()) : [];
  const contractPanel = page.querySelector('[data-testid="contract-panel"]');
  const routes = contractPanel
    ? [...contractPanel.querySelectorAll('[data-testid="contract-route"]')] : [];
  const routeCount = routes.length;
  const paramCount = routes.reduce(
    (n, r) => n + [...r.querySelectorAll('table tbody tr')]
      .filter(row => !row.closest('[data-testid="error-codes-table"]')).length, 0);
  const errorToggles = routes
    .map(r => r.querySelector('[data-testid="error-codes-toggle"]'))
    .filter(Boolean);
  const errorCount = errorToggles.reduce((n, b) => {
    const m = b.textContent.match(/\((\d+)\)/);
    return n + (m ? Number(m[1]) : 0);
  }, 0);
  const sectionTitles = routes.length
    ? [...routes[0].querySelectorAll('.MuiTypography-overline')].map(el => el.textContent.trim())
    : [];
  const errorTableRows = contractPanel
    ? contractPanel.querySelectorAll('[data-testid="error-codes-table"] tbody tr').length : 0;
  const generatedNote = contractPanel
    ? [...contractPanel.querySelectorAll('span, p')]
        .map(el => el.textContent.trim())
        .find(text => text === 'derived statically, not model-generated') || ''
    : '';
  const body = page.children[1] || null;
  const description = body ? (body.querySelector('p')?.textContent.trim() || '') : '';
  const methodNames = [...page.querySelectorAll('[data-testid^="key-method-"]')]
    .map(el => el.querySelector('p')?.textContent.trim() || '');
  return {
    present: true,
    method: chip ? chip.textContent.trim() : '',
    path: headerTexts[0] || '',
    title: headerTexts[1] || '',
    description,
    routeCount,
    paramCount,
    errorCount,
    errorTableRows,
    sectionTitles,
    generatedNote,
    methodNames,
  };
}
"""


READ_METHOD_CODE = """
() => {
  const el = document.querySelector('[data-testid="method-code"]');
  if (!el) return { present: false };
  const view = el.querySelector('[data-testid="code-view"]');
  const text = (view ? view.innerText : el.innerText) || '';
  return { present: true, fqn: view ? view.getAttribute('data-fqn') : '', text };
}
"""


READ_SIDEBAR = """
() => {
  const root = document.querySelector('[data-testid="endpoint-sidebar"]');
  if (!root) return { present: false, rows: [] };
  const rows = [...root.querySelectorAll('[data-testid^="sidebar-endpoint-"]')].map(el => ({
    testid: el.getAttribute('data-testid'),
    active: el.getAttribute('data-active'),
    label: el.querySelector('p')?.textContent.trim() || '',
  }));
  return { present: true, rows };
}
"""
