export const ELEMENTAL_ATTACK_MODIFIER = 20;
export const FONT_BASE_SIZE = 16;
export const DECK_MAX_LENGTH = 40;

// Menus

interface NavLink {
    href?: string | null;
    label: string;
    subMenu?: NavLink[] | null;
}

export const NAV_LINKS:NavLink[] = [
    { href: '/my-collection', label: 'My collection' },
    { href: '/cards-and-sets', label: 'Cards & Sets'},
    { href: '#', label: 'Rewards' },
    { href: '#', label: 'How to play' },
    { href: '/lobby', label: 'Jugar' },
    {
        label: 'Dev',
        subMenu: [
            { href: '/old/cards/create', label: 'Crear Carta' },
            { href: '/old/attacks/create', label: 'Crear Ataque' },
            { href: '/old/abilities/create', label: 'Crear Habilidad' },
            { href: '/old/associations/create', label: 'Crear Asociación' },
            { href: '/old/cards', label: 'Cartas' },
            { href: '/old/clasification', label: 'Clasificación' },
            { href: '/old/attacks', label: 'Ataques' },
            { href: '/old/abilities', label: 'Habilidades' },
            { href: '/old/associations', label: 'Asociaciones' },
            { href: '/old/decks', label: 'Mazos' },
        ]
    },
] as const;

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