/**
 * Helper to get auth headers from server locals
 * Use this in +page.server.ts load functions
 */
export function getAuthHeaders(locals: App.Locals): Record<string, string> {
	const headers: Record<string, string> = {};
	if (locals.token) {
		headers['Authorization'] = `Bearer ${locals.token}`;
	}
	return headers;
}

