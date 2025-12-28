import type { Handle } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import { setCurrentRoute } from '$lib/api';
import { NO_AUTH_ROUTES } from '$lib/constants';

const TOKEN_KEY = 'auth_token';

export const handle: Handle = async ({ event, resolve }) => {
	// Get token from cookie
	const token = event.cookies.get(TOKEN_KEY);

	// Store token in locals so it's accessible in load functions
	event.locals.token = token ?? null;

	const path = event.url.pathname;
	
	// Set current route for API interceptor to check for redirect loops
	setCurrentRoute(path);
	
	const isPublicRoute = NO_AUTH_ROUTES.some((route) => path.startsWith(route));

	// Redirect to login if accessing protected route without token
	if (!isPublicRoute && !token) {
		throw redirect(302, '/login');
	}

	return resolve(event);
};

