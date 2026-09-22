/**
 * Minimal vanilla-JS frontend. Purpose is to confirm the API works
 * end-to-end (per the task brief, styling/design isn't evaluated), so this
 * intentionally stays framework-free with no build step.
 *
 * Tokens are kept in localStorage for simplicity in this demo. A production
 * app would prefer httpOnly cookies to reduce XSS exposure - noted in the
 * README under "what I'd do differently".
 */

const API_BASE = '/api';
let currentPage = 1;

// ---------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------
const getAccessToken = () => localStorage.getItem('access');
const getRefreshToken = () => localStorage.getItem('refresh');

function setTokens({ access, refresh }) {
    localStorage.setItem('access', access);
    if (refresh) localStorage.setItem('refresh', refresh);
}

function clearTokens() {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('username');
}

// ---------------------------------------------------------------------
// Fetch wrapper: attaches the JWT, and transparently retries once after
// refreshing the access token on a 401 (access token expired mid-session).
// ---------------------------------------------------------------------
async function apiFetch(path, options = {}, retry = true) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    const token = getAccessToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (response.status === 401 && retry && getRefreshToken()) {
        const refreshed = await tryRefreshToken();
        if (refreshed) return apiFetch(path, options, false);
        logout();
    }
    return response;
}

async function tryRefreshToken() {
    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: getRefreshToken() }),
        });
        const body = await response.json();
        if (response.ok) {
            setTokens(body.data);
            return true;
        }
    } catch (e) { /* fall through to logout */ }
    return false;
}

// ---------------------------------------------------------------------
// Auth UI
// ---------------------------------------------------------------------
const authSection = document.getElementById('auth-section');
const appSection = document.getElementById('app-section');
const authMessage = document.getElementById('auth-message');

function showMessage(el, text, type) {
    el.textContent = text;
    el.className = `message ${type}`;
}

document.getElementById('tab-login').addEventListener('click', () => switchTab('login'));
document.getElementById('tab-signup').addEventListener('click', () => switchTab('signup'));

function switchTab(tab) {
    document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
    document.getElementById('signup-form').classList.toggle('hidden', tab !== 'signup');
    document.getElementById('tab-login').classList.toggle('active', tab === 'login');
    document.getElementById('tab-signup').classList.toggle('active', tab === 'signup');
    authMessage.textContent = '';
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });
    const body = await response.json();
    if (response.ok) {
        setTokens(body.data);
        localStorage.setItem('username', username);
        enterApp(username);
    } else {
        showMessage(authMessage, body.message || 'Login failed', 'error');
    }
});

document.getElementById('signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        username: document.getElementById('signup-username').value,
        email: document.getElementById('signup-email').value,
        password: document.getElementById('signup-password').value,
        confirm_password: document.getElementById('signup-confirm-password').value,
    };
    const response = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (response.ok) {
        showMessage(authMessage, 'Account created — you can log in now.', 'success');
        switchTab('login');
    } else {
        showMessage(authMessage, flattenErrors(body), 'error');
    }
});

document.getElementById('logout-btn').addEventListener('click', logout);

function logout() {
    clearTokens();
    appSection.classList.add('hidden');
    authSection.classList.remove('hidden');
}

function enterApp(username) {
    authSection.classList.add('hidden');
    appSection.classList.remove('hidden');
    document.getElementById('whoami').textContent = `Logged in as ${username}`;
    document.getElementById('expense-date').valueAsDate = new Date();
    document.getElementById('summary-month').value = new Date().toISOString().slice(0, 7);
    loadCategories();
    loadSummary();
    loadExpenses();
}

function flattenErrors(body) {
    if (body.errors) {
        return Object.entries(body.errors)
            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(' ') : msgs}`)
            .join(' | ');
    }
    return body.message || 'Something went wrong.';
}

// ---------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------
async function loadCategories() {
    const response = await apiFetch('/categories');
    const body = await response.json();
    if (!response.ok) return;

    const categories = body.data || [];
    const expenseSelect = document.getElementById('expense-category');
    const filterSelect = document.getElementById('filter-category');

    expenseSelect.innerHTML = categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    filterSelect.innerHTML = '<option value="">All categories</option>' +
        categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
}

document.getElementById('category-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const nameInput = document.getElementById('category-name');
    const msgEl = document.getElementById('category-message');

    const response = await apiFetch('/categories', {
        method: 'POST',
        body: JSON.stringify({ name: nameInput.value }),
    });
    const body = await response.json();
    if (response.ok) {
        showMessage(msgEl, `"${body.data.name}" added.`, 'success');
        nameInput.value = '';
        loadCategories();
    } else {
        showMessage(msgEl, flattenErrors(body), 'error');
    }
});

// ---------------------------------------------------------------------
// Expenses
// ---------------------------------------------------------------------
document.getElementById('expense-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const msgEl = document.getElementById('expense-message');
    const payload = {
        amount: document.getElementById('expense-amount').value,
        category: document.getElementById('expense-category').value,
        date: document.getElementById('expense-date').value,
        note: document.getElementById('expense-note').value,
    };

    const response = await apiFetch('/expenses', { method: 'POST', body: JSON.stringify(payload) });
    const body = await response.json();
    if (response.ok) {
        showMessage(msgEl, 'Expense added.', 'success');
        document.getElementById('expense-amount').value = '';
        document.getElementById('expense-note').value = '';
        loadSummary();
        loadExpenses();
    } else {
        showMessage(msgEl, flattenErrors(body), 'error');
    }
});

document.getElementById('filter-apply-btn').addEventListener('click', () => {
    currentPage = 1;
    loadExpenses();
});

document.getElementById('prev-page-btn').addEventListener('click', () => {
    if (currentPage > 1) { currentPage -= 1; loadExpenses(); }
});
document.getElementById('next-page-btn').addEventListener('click', () => {
    currentPage += 1;
    loadExpenses();
});

async function loadExpenses() {
    const category = document.getElementById('filter-category').value;
    const startDate = document.getElementById('filter-start-date').value;
    const endDate = document.getElementById('filter-end-date').value;

    const params = new URLSearchParams({ page: currentPage });
    if (category) params.set('category', category);
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);

    const response = await apiFetch(`/expenses?${params.toString()}`);
    const body = await response.json();
    if (!response.ok) return;

    const { results, next, previous } = body.data;
    const tbody = document.getElementById('expense-table-body');
    tbody.innerHTML = results.map(exp => `
        <tr>
            <td>${exp.date}</td>
            <td>${exp.category_name}</td>
            <td>${exp.amount}</td>
            <td>${exp.note || '-'}</td>
        </tr>
    `).join('') || '<tr><td colspan="4">No expenses found.</td></tr>';

    document.getElementById('page-indicator').textContent = `Page ${currentPage}`;
    document.getElementById('prev-page-btn').disabled = !previous;
    document.getElementById('next-page-btn').disabled = !next;
}

// ---------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------
document.getElementById('summary-refresh-btn').addEventListener('click', loadSummary);

async function loadSummary() {
    const month = document.getElementById('summary-month').value;
    const output = document.getElementById('summary-output');
    output.textContent = 'Loading...';

    const params = month ? `?month=${month}` : '';
    const response = await apiFetch(`/summary${params}`);
    const body = await response.json();
    if (!response.ok) {
        output.textContent = flattenErrors(body);
        return;
    }

    const data = body.data;
    const changeText = data.mom_change_percent === null
        ? data.mom_change_note
        : `${data.mom_change_percent > 0 ? '+' : ''}${data.mom_change_percent}% vs last month`;

    output.innerHTML = `
        <div class="total">₹${data.total_spend} <small>(${changeText})</small></div>
        <table>
            <thead><tr><th>Category</th><th>Total</th></tr></thead>
            <tbody>
                ${data.by_category.map(c => `<tr><td>${c.category}</td><td>₹${c.total}</td></tr>`).join('') || '<tr><td colspan="2">No expenses yet.</td></tr>'}
            </tbody>
        </table>
        ${data.insights.map(i => `<div class="insight">⚠ ${i.message}</div>`).join('')}
    `;
}

// ---------------------------------------------------------------------
// Boot: resume session if a token is already stored
// ---------------------------------------------------------------------
if (getAccessToken() && localStorage.getItem('username')) {
    enterApp(localStorage.getItem('username'));
}
