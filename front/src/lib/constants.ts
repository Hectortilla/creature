export const ELEMENTAL_ATTACK_MODIFIER = 20;
export const FONT_BASE_SIZE = 16;

export const COLLECTION_MENU = [
    { label: 'My Cards', submenu_label: 'Cards', amount_label: 'cards', image: 'cards', path: '/my-collection/cards' },
    { label: 'My Decks', submenu_label: 'Decks', amount_label: 'decks', image: 'decks', path: '/my-collection/decks' },
    { label: 'My Accesories', submenu_label: 'Accesories', amount_label: 'cards', image: 'cards', path: '/my-collection/car' },
    { label: 'My Wishlist', submenu_label: 'Wishlist', amount_label: 'decks', image: 'decks', path: '/my-collection/dec' },
] as const;

/**
 * Routes that don't require authentication
 * These routes are accessible without a valid auth token
 */
export const NO_AUTH_ROUTES = ['/login', '/register'] as const;