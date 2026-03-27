import { goto } from '$app/navigation';
import { browser } from '$app/environment';

export function getToken(): string | null {
	if (!browser) return null;
	return localStorage.getItem('access_token');
}

export function isTokenExpired(token: string): boolean {
	try {
		const payload = JSON.parse(atob(token.split('.')[1]));
		return payload.exp * 1000 < Date.now();
	} catch {
		return true;
	}
}

export function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
	const token = getToken();
	const h: Record<string, string> = { 'Content-Type': 'application/json', ...extra };
	if (token) h['Authorization'] = `Bearer ${token}`;
	return h;
}

export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
	if (browser) {
		const token = getToken();
		if (token && isTokenExpired(token)) {
			localStorage.removeItem('access_token');
			goto('/login');
			throw new Error('Session expired. Please log in again.');
		}
	}

	const res = await fetch(url, {
		...options,
		headers: { ...authHeaders(), ...(options.headers as Record<string, string> || {}) }
	});

	if (res.status === 401 && browser) {
		localStorage.removeItem('access_token');
		goto('/login');
		throw new Error('Session expired. Please log in again.');
	}

	return res;
}
