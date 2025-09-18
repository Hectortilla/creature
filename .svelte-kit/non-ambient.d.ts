
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/abilities" | "/abilities/create" | "/abilities/[ability]" | "/api" | "/api/abilities" | "/api/associations" | "/api/attacks" | "/api/cards" | "/api/characters" | "/api/elements" | "/api/types" | "/associations" | "/associations/create" | "/associations/[association]" | "/attacks" | "/attacks/create" | "/attacks/[attack]" | "/cards" | "/cards/create" | "/cards/[card]" | "/cards/[card]/edit" | "/clasification";
		RouteParams(): {
			"/abilities/[ability]": { ability: string };
			"/associations/[association]": { association: string };
			"/attacks/[attack]": { attack: string };
			"/cards/[card]": { card: string };
			"/cards/[card]/edit": { card: string }
		};
		LayoutParams(): {
			"/": { ability?: string; association?: string; attack?: string; card?: string };
			"/abilities": { ability?: string };
			"/abilities/create": Record<string, never>;
			"/abilities/[ability]": { ability: string };
			"/api": Record<string, never>;
			"/api/abilities": Record<string, never>;
			"/api/associations": Record<string, never>;
			"/api/attacks": Record<string, never>;
			"/api/cards": Record<string, never>;
			"/api/characters": Record<string, never>;
			"/api/elements": Record<string, never>;
			"/api/types": Record<string, never>;
			"/associations": { association?: string };
			"/associations/create": Record<string, never>;
			"/associations/[association]": { association: string };
			"/attacks": { attack?: string };
			"/attacks/create": Record<string, never>;
			"/attacks/[attack]": { attack: string };
			"/cards": { card?: string };
			"/cards/create": Record<string, never>;
			"/cards/[card]": { card: string };
			"/cards/[card]/edit": { card: string };
			"/clasification": Record<string, never>
		};
		Pathname(): "/" | "/abilities" | "/abilities/" | "/abilities/create" | "/abilities/create/" | `/abilities/${string}` & {} | `/abilities/${string}/` & {} | "/api" | "/api/" | "/api/abilities" | "/api/abilities/" | "/api/associations" | "/api/associations/" | "/api/attacks" | "/api/attacks/" | "/api/cards" | "/api/cards/" | "/api/characters" | "/api/characters/" | "/api/elements" | "/api/elements/" | "/api/types" | "/api/types/" | "/associations" | "/associations/" | "/associations/create" | "/associations/create/" | `/associations/${string}` & {} | `/associations/${string}/` & {} | "/attacks" | "/attacks/" | "/attacks/create" | "/attacks/create/" | `/attacks/${string}` & {} | `/attacks/${string}/` & {} | "/cards" | "/cards/" | "/cards/create" | "/cards/create/" | `/cards/${string}` & {} | `/cards/${string}/` & {} | `/cards/${string}/edit` & {} | `/cards/${string}/edit/` & {} | "/clasification" | "/clasification/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/.DS_Store" | "/images/.DS_Store" | "/images/card-mask.svg" | "/images/cards/bruja.jpg" | "/images/cards/cabeza-de-medusa.jpg" | "/images/cards/come-metal.jpg" | "/images/cards/dragon.jpg" | "/images/cards/hada-del-bosque.jpg" | "/images/cards/placeholder.jpg" | "/images/elements/air.png" | "/images/elements/darkness.png" | "/images/elements/ether.png" | "/images/elements/fire.png" | "/images/elements/ground.png" | "/images/elements/ice.png" | "/images/elements/light.png" | "/images/elements/metal.png" | "/images/elements/nature.png" | "/images/elements/thunder.png" | "/images/elements/water.png" | "/images/finger-prints/1.jpg" | "/images/finger-prints/2.jpg" | "/images/finger-prints/3.jpg" | "/images/finger-prints/4.jpg" | "/robots.txt" | "/uploads/come_mucho_metal.jpg" | "/uploads/espada-musgo.jpg" | "/uploads/gigante_de_hierro.jpg" | "/uploads/guerrero_de_fuego-test.jpg" | "/uploads/guerrero_de_fuego.jpg" | "/uploads/heraldo-del-rayo.jpg" | "/uploads/test-over.png" | "/uploads/traga-metal.jpg" | "/uploads/urgo-el-oso-1.jpg" | "/uploads/urgo-el-oso-2.jpg" | string & {};
	}
}