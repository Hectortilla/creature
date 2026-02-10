export const ELEMENTAL_ATTACK_MODIFIER = 20;
export const FONT_BASE_SIZE = 16;

export const COLLECTION_MENU = [
    { name: 'My Cards', path: '/collection/cards', amount_label: 'cards', image: 'cards' },
    { name: 'My Decks', path: '/collection/decks', amount_label: 'decks', image: 'decks' },
] as const;

/**
 * Routes that don't require authentication
 * These routes are accessible without a valid auth token
 */
export const NO_AUTH_ROUTES = ['/login', '/register'] as const;