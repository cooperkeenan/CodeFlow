READ_ENDPOINT_DETAIL = """
() => {
  const page = document.querySelector('[data-testid="endpoint-page"]');
  if (!page) return { present: false };
  const header = page.querySelector('header');
  const chip = header ? header.querySelector('.MuiChip-label') : null;
  const headerTexts = header ? [...header.querySelectorAll('p')].map(p => p.textContent.trim()) : [];
  const contractPanel = page.querySelector('[data-testid="contract-panel"]');
  const heading = (text) => {
    if (!contractPanel) return null;
    return [...contractPanel.querySelectorAll('h6, .MuiTypography-h6')]
      .find(h => h.textContent.trim() === text) || null;
  };
  const paramCount = contractPanel ? contractPanel.querySelectorAll('table tbody tr').length : 0;
  const responsesHeading = heading('Responses');
  const responseCount = responsesHeading && responsesHeading.nextElementSibling
    ? responsesHeading.nextElementSibling.children.length : 0;
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
    paramCount,
    responseCount,
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
