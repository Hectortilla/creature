/**
 * Pattern matcher for section: card, attack.
 * In the string format of players.
 *
 * @see https://svelte.dev/docs/kit/advanced-routing#Matching
 */
import type { ParamMatcher } from "@sveltejs/kit";

const params = ["cards", "attacks", "elements"] as const;

export const match = ((param: string): param is (typeof params)[number] => {
    return params.includes(param as any);
}) satisfies ParamMatcher;