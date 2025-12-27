import { browser } from '$app/environment';
import type { UserRead } from '$lib/api/types.gen';

export const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

// Re-export UserRead as User for convenience
export type User = UserRead;

// Helper to set cookie
function setCookie(name: string, value: string, days: number = 7) {
	if (!browser) return;
	const expires = new Date(Date.now() + days * 864e5).toUTCString();
	document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

// Helper to delete cookie
function deleteCookie(name: string) {
	if (!browser) return;
	document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
}

// Create reactive state using Svelte 5 runes
function createAuthStore() {
	// Initialize from localStorage if in browser
	let token = $state<string | null>(browser ? localStorage.getItem(TOKEN_KEY) : null);
	let user = $state<User | null>(
		browser ? JSON.parse(localStorage.getItem(USER_KEY) || 'null') : null
	);

	// Derived state
	const isAuthenticated = $derived(!!token && !!user);

	function setAuth(newToken: string, newUser: User) {
		token = newToken;
		user = newUser;

		if (browser) {
			// Store in localStorage for client-side access
			localStorage.setItem(TOKEN_KEY, newToken);
			localStorage.setItem(USER_KEY, JSON.stringify(newUser));
			// Store in cookie for server-side access
			setCookie(TOKEN_KEY, newToken);
		}
	}

	function clearAuth() {
		token = null;
		user = null;

		if (browser) {
			localStorage.removeItem(TOKEN_KEY);
			localStorage.removeItem(USER_KEY);
			deleteCookie(TOKEN_KEY);
		}
	}

	return {
		get user() {
			return user;
		},
		get isAuthenticated() {
			return isAuthenticated;
		},
		setAuth,
		clearAuth,
	};
}

export const auth = createAuthStore();

