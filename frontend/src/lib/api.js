const API_BASE = 'http://localhost:8000';

/**
 * Helper function untuk fetch API.
 * Semua request ke backend melewati fungsi ini.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  const res = await fetch(url, config);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Server error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/** POST /api/predict — kirim data transaksi, terima prediksi fraud */
export function predictTransaction(data) {
  return request('/api/predict', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/** GET /api/transactions — ambil daftar transaksi */
export function getTransactions(status = null, limit = 20, offset = 0) {
  let query = `?limit=${limit}&offset=${offset}`;
  if (status) query += `&status=${status}`;
  return request(`/api/transactions${query}`);
}

/** PATCH /api/transactions/:id — update status */
export function updateTransactionStatus(id, status) {
  return request(`/api/transactions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

/** GET /api/dashboard/stats — ambil statistik dashboard */
export function getDashboardStats() {
  return request('/api/dashboard/stats');
}

/** POST /api/chat — kirim pesan ke chatbot */
export function sendChatMessage(message, sessionId) {
  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId }),
  });
}
