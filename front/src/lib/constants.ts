export const ELEMENTAL_ATTACK_MODIFIER = 20;

/**
 * Routes that don't require authentication
 * These routes are accessible without a valid auth token
 */
export const NO_AUTH_ROUTES = ['/login', '/register'] as const;