// Client-side hooks
// Route protection is handled by hooks.server.ts
// This file can be used for client-specific error handling if needed

import type { HandleClientError } from '@sveltejs/kit';

export const handleError: HandleClientError = ({ error }) => {
	console.error('Client error:', error);
	return {
		message: 'An unexpected error occurred'
	};
};

