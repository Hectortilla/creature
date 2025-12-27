import { PUBLIC_API_URL } from '$env/static/public';
import { browser } from '$app/environment';
import { client } from './api/client.gen';
import { auth } from './stores/auth.svelte';

const TOKEN_KEY = 'auth_token';

// Configure the API client with the base URL from environment
export function configureApiClient(baseUrl: string = PUBLIC_API_URL) {
	client.setConfig({
		baseUrl,
		credentials: 'include' as RequestCredentials // Include credentials for CORS
	});

	// Add request interceptor to inject auth token (client-side only)
	// Server-side requests pass the token via headers in load functions
	client.interceptors.request.use((request) => {
		if (browser) {
			const token = localStorage.getItem(TOKEN_KEY);
			if (token) {
				request.headers.set('Authorization', `Bearer ${token}`);
			}
		}
		return request;
	});

	// Add response interceptor to handle 401 errors
	client.interceptors.error.use((error, response, request) => {
		if (response?.status === 401) {
			// Don't redirect for auth endpoints (login/register) to avoid loops
			const url = request?.url || '';
			const isAuthEndpoint = url.includes('/auth/token') || url.includes('/auth/register');
			
			if (!isAuthEndpoint) {
				// Clear auth state on unauthorized
				auth.clearAuth();
				// Redirect to login (only on client-side to avoid server-side redirect loops)
				if (browser) {
					// Check if we're already on a public route to avoid redirect loops
					const currentPath = window.location.pathname;

					const isPublicRoute = currentPath === '/login' || currentPath === '/register';
					
					if (!isPublicRoute) {
						// Client-side redirect
						window.location.href = '/login';
					}
				}
				// Note: Server-side 401s will propagate as errors to load functions
				// which can handle them appropriately without causing redirect loops
			}
		}
		return error;
	});
}

// Initialize with default config
configureApiClient();

// Auth API functions (not auto-generated, manual implementation)
export async function loginApi(username: string, password: string) {
	const formData = new URLSearchParams();
	formData.append('username', username);
	formData.append('password', password);

	const response = await fetch(`${PUBLIC_API_URL}/auth/token`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded'
		},
		body: formData
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Login failed');
	}

	return response.json();
}

export async function registerApi(userData: {
	username: string;
	password: string;
	email?: string;
	full_name?: string;
}) {
	const response = await fetch(`${PUBLIC_API_URL}/auth/register`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(userData)
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Registration failed');
	}

	return response.json();
}

export async function getMeApi(token: string) {
	const response = await fetch(`${PUBLIC_API_URL}/auth/me`, {
		method: 'GET',
		headers: {
			Authorization: `Bearer ${token}`
		}
	});

	if (!response.ok) {
		throw new Error('Failed to get user info');
	}

	return response.json();
}

// Re-export everything from the generated SDK
export * from './api/sdk.gen';
export * from './api/types.gen';
