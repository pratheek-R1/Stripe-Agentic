/* ─── Paygentic – script.js ──────────────────────────────────────────────── */
'use strict';

// ── API URL ─────────────────────────────────────────────────────────────────
// Relative path → works when served via serve.py (http://localhost:5500).
// The serve.py proxy forwards this to http://localhost:8000/create_payment_nl.
const API_URL = '/create_payment_nl';

// ── DOM refs (with null guard) ───────────────────────────────────────────────
function $(id) {
  const el = document.getElementById(id);
  if (!el) console.error('[Paygentic] Missing element: #' + id);
  return el;
}

const promptInput   = $('prompt-input');
const charCount     = $('char-count');
const generateBtn   = $('generate-btn');
const btnLabel      = $('btn-label');
const btnSpinner    = $('btn-spinner');
const resultSection = $('result-section');
const errorBox      = $('error-box');
const errorMsg      = $('error-msg');
const successBox    = $('success-box');
const detailsWrap   = $('details-wrap');
const checkoutLink  = $('checkout-link');   // <a> element
const linkDisplay   = $('link-display');
const copyBtn       = $('copy-btn');
const chips         = document.querySelectorAll('.chip');

// ── Suggestion chips ─────────────────────────────────────────────────────────
chips.forEach(chip => {
  chip.addEventListener('click', () => {
    promptInput.value = chip.dataset.prompt;
    promptInput.dispatchEvent(new Event('input'));
    promptInput.focus();
    chip.style.background = 'rgba(99,102,241,0.2)';
    setTimeout(() => { chip.style.background = ''; }, 300);
  });
});

// ── Character counter + enable button ────────────────────────────────────────
promptInput.addEventListener('input', () => {
  const len = promptInput.value.length;
  charCount.textContent = len + ' / 500';
  charCount.style.color = len > 450 ? '#f43f5e' : '';
  generateBtn.disabled = !promptInput.value.trim();
});

// ── Auto-resize textarea ──────────────────────────────────────────────────────
promptInput.addEventListener('input', () => {
  promptInput.style.height = 'auto';
  promptInput.style.height = Math.min(promptInput.scrollHeight, 260) + 'px';
});

// ── Ctrl/Cmd + Enter ─────────────────────────────────────────────────────────
promptInput.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    if (!generateBtn.disabled) generateBtn.click();
  }
});

// ── Loading state ────────────────────────────────────────────────────────────
function setLoading(on) {
  generateBtn.disabled = on;
  generateBtn.classList.toggle('loading', on);
  btnSpinner.classList.toggle('hidden', !on);
  btnLabel.textContent = on ? 'Generating…' : 'Generate Payment Link';
}

// ── Show / hide result area ───────────────────────────────────────────────────
// Uses ONLY inline styles – bypasses all Tailwind / CSS-class specificity issues.
function reveal(el) {
  if (!el) return;
  el.style.removeProperty('display');  // clear any previous inline hide
  el.style.display = 'block';
  el.style.opacity = '1';
  el.style.transform = 'none';
  el.style.pointerEvents = 'auto';
}

function conceal(el) {
  if (!el) return;
  el.style.display = 'none';
}

function showSuccess() {
  console.log('[Paygentic] showSuccess()');
  reveal(resultSection);
  conceal(errorBox);
  reveal(successBox);
}

function showError(msg) {
  console.log('[Paygentic] showError():', msg);
  errorMsg.textContent = msg;
  reveal(resultSection);
  reveal(errorBox);
  conceal(successBox);
}

function hideAll() {
  conceal(resultSection);
  conceal(errorBox);
  conceal(successBox);
}

// ── Optimistic parse state ────────────────────────────────────────────────────
let extractedAmount  = null;
let extractedProduct = null;
let extractedEmail   = null;
let extractedQty     = 1;

// ── Build detail badges ───────────────────────────────────────────────────────
function buildDetails() {
  detailsWrap.innerHTML = '';
  const fields = [
    { label: '💰 Amount',  value: extractedAmount  != null ? '$' + extractedAmount : '—', cls: 'badge-amount'  },
    { label: '📦 Product', value: extractedProduct || '—',                                cls: 'badge-product' },
    { label: '✉️ Email',  value: extractedEmail   || '—',                                cls: 'badge-email'   },
    { label: '🔢 Qty',     value: String(extractedQty || 1),                              cls: 'badge-qty'     },
  ];
  fields.forEach((f, i) => {
    const badge = document.createElement('span');
    badge.className = 'detail-badge ' + f.cls;
    badge.style.animationDelay = (i * 0.07) + 's';
    badge.innerHTML = '<span style="opacity:0.7;font-size:0.75em">' + f.label + '</span> ' + f.value;
    detailsWrap.appendChild(badge);
  });
  console.log('[Paygentic] Badges built.');
}

// ── Copy button ───────────────────────────────────────────────────────────────
copyBtn.addEventListener('click', async () => {
  const url = linkDisplay.textContent.trim();
  if (!url || url === '—') return;
  try {
    await navigator.clipboard.writeText(url);
    copyBtn.textContent = '✓ Copied';
    copyBtn.style.color = '#34d399';
    setTimeout(() => {
      copyBtn.textContent = 'Copy';
      copyBtn.style.color = '';
    }, 1800);
  } catch (err) {
    console.warn('[Paygentic] Clipboard failed:', err.message);
  }
});

// ── Main click handler ────────────────────────────────────────────────────────
generateBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  e.stopPropagation();

  const prompt = promptInput.value.trim();
  if (!prompt) return;

  console.log('[Paygentic] ── New request ──────────────────────');
  console.log('[Paygentic] Prompt:', prompt);

  setLoading(true);
  hideAll();

  // Optimistic parse
  const amtMatch  = prompt.match(/\$?([\d,]+(?:\.\d{1,2})?)/);
  const emlMatch  = prompt.match(/[\w.+-]+@[\w-]+\.[a-z]{2,}/i);
  const prodMatch = prompt.match(/for\s+(.+?)\s+(?:for|to)\s+/i)
                 || prompt.match(/(?:invoice|bill|charge)\s+(?:for\s+)?(.+?)(?:\s+(?:for|to)\s+|$)/i);

  extractedAmount  = amtMatch  ? parseFloat(amtMatch[1].replace(',', '')) : null;
  extractedEmail   = emlMatch  ? emlMatch[0] : null;
  extractedProduct = prodMatch ? prodMatch[1].replace(/\s+(?:for|to)\s+.+$/i, '').trim() : null;
  extractedQty     = 1;

  console.log('[Paygentic] Parsed:', { extractedAmount, extractedEmail, extractedProduct });

  let data;

  try {
    console.log('[Paygentic] Fetching:', API_URL);

    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });

    console.log('[Paygentic] HTTP status:', res.status, res.statusText);

    const text = await res.text();
    console.log('[Paygentic] Raw response text:', text);

    try {
      data = JSON.parse(text);
    } catch (parseErr) {
      throw new Error('Backend returned non-JSON: ' + text.slice(0, 200));
    }

    console.log('[Paygentic] Parsed data:', data);

  } catch (fetchErr) {
    console.error('[Paygentic] Fetch error:', fetchErr.name, fetchErr.message);

    let msg = fetchErr.message;
    if (fetchErr instanceof TypeError) {
      msg = 'Network error – cannot reach the backend.\n\n'
          + 'Make sure:\n'
          + '1. run_agents.py is running (port 8000)\n'
          + '2. You opened this page via serve.py (http://localhost:5500)\n'
          + '   NOT as a file:// URL';
    }
    showError(msg);
    setLoading(false);
    generateBtn.disabled = !promptInput.value.trim();
    return;
  }

  // ── Render result ──────────────────────────────────────────────────────────
  try {
    const rawLink   = (data && data.payment_link) ? String(data.payment_link) : '';
    const validLink = rawLink.startsWith('http') ? rawLink : '';

    console.log('[Paygentic] status:', data.status, '| link:', rawLink);

    if (data.status === 'success' && validLink) {
      buildDetails();

      linkDisplay.textContent = validLink;
      checkoutLink.href       = validLink;
      checkoutLink.setAttribute('href', validLink);   // belt-and-suspenders

      console.log('[Paygentic] checkout href →', checkoutLink.href);
      showSuccess();

    } else {
      const errMsg = (data && typeof data.details === 'string' && data.details)
        ? data.details
        : 'Payment link not returned. status=' + (data && data.status);
      showError(errMsg);
    }

  } catch (renderErr) {
    console.error('[Paygentic] Render error:', renderErr.name, renderErr.message, renderErr.stack);
    showError('UI render error: ' + renderErr.message);
  }

  setLoading(false);
  generateBtn.disabled = !promptInput.value.trim();
  console.log('[Paygentic] ── Done ────────────────────────────');
});

// ── Init ─────────────────────────────────────────────────────────────────────
generateBtn.disabled = true;
hideAll();
console.log('[Paygentic] Ready. API →', API_URL);
