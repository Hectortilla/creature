import type { Handle } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';

const TOKEN_KEY = 'auth_token';

// Public routes that don't require authentication
const publicRoutes = ['/login', '/register'];

export const handle: Handle = async ({ event, resolve }) => {
	// Get token from cookie
	const token = event.cookies.get(TOKEN_KEY);

	// Store token in locals so it's accessible in load functions
	event.locals.token = token ?? null;

	const path = event.url.pathname;
	const isPublicRoute = publicRoutes.some((route) => path.startsWith(route));

	// Redirect to login if accessing protected route without token
	if (!isPublicRoute && !token) {
		throw redirect(302, '/login');
	}

	// Redirect to home if accessing auth pages while logged in
	if (isPublicRoute && token) {
		throw redirect(302, '/');
	}

	return resolve(event);
};

