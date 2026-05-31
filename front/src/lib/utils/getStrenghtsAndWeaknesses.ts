import type { Element } from "$lib/types";
import { ELEMENTAL_ATTACK_MODIFIER } from "$lib/constants";

export type Relation = {
	element: Element;
	value: number; // magnitud: 20, 40 etc. (positiva; signada en el cálculo interno)
};

/**
 * Comparación segura de ids (soporta number o bigint) usando string.
 */
function sameId(a: unknown, b: unknown): boolean {
	return String(a) === String(b);
}

/**
 * Calcula el mapa neto de relaciones (positivo = ventaja de la carta contra ese elemento de ataque,
 * negativo = desventaja). Devuelve array de { element, value } con sign en value.
 */
function computeNetRelations(
	allElements: Element[],
	first: Element | null = null,
	second: Element | null = null,
): { element: Element; value: number }[] {
	const cardElements = [first, second].filter(Boolean) as Element[];
	if (cardElements.length === 0) return [];

	const results: { element: Element; value: number }[] = [];

	for (const attackEl of allElements) {
		// ignorar si el attack element es igual a alguno de los elementos de la carta
		if (cardElements.some((ce) => sameId(ce.id, attackEl.id))) continue;

		let net = 0;

		for (const cardEl of cardElements) {
			// Si el elemento atacante es débil frente al elemento de la carta => ventaja para la carta
			if (
				Array.isArray(attackEl.weaknesses) &&
				attackEl.weaknesses.some((w) => sameId(w, cardEl.id))
			) {
				net += ELEMENTAL_ATTACK_MODIFIER;
			}

			// Si el elemento atacante es fuerte frente al elemento de la carta => desventaja para la carta
			if (
				Array.isArray(attackEl.strengths) &&
				attackEl.strengths.some((s) => sameId(s, cardEl.id))
			) {
				net -= ELEMENTAL_ATTACK_MODIFIER;
			}
		}

		if (net !== 0) {
			results.push({ element: attackEl, value: net }); // value puede ser -20, -40, +20, +40
		}
	}

	return results;
}

/**
 * Devuelve fortalezas de la carta: elementos contra los que la carta tiene ventaja.
 * value es la magnitud positiva (20, 40...)
 */
export function getCardStrengths(
	allElements: Element[],
	first: Element | null = null,
	second: Element | null = null,
): Relation[] {
	const net = computeNetRelations(allElements, first, second);
	return net
		.filter((r) => r.value > 0)
		.map((r) => ({ element: r.element, value: r.value })); // value positivo
}

/**
 * Devuelve debilidades de la carta: elementos contra los que la carta tiene desventaja.
 * value es la magnitud positiva (20, 40...)
 */
export function getCardWeaknesses(
	allElements: Element[],
	first: Element | null = null,
	second: Element | null = null,
): Relation[] {
	const net = computeNetRelations(allElements, first, second);
	return net
		.filter((r) => r.value < 0)
		.map((r) => ({ element: r.element, value: Math.abs(r.value) })); // convertimos a magnitud positiva
}

/**
 * Mapea fortalezas de un ataque a elementos completos con value fijo = 20
 */
export function getAttackStrengths(
	allElements: Element[],
	element: Element | null,
): Relation[] {
	if (!element || !Array.isArray(element.strengths)) return [];

	return element.strengths
		.map((id) => {
			const el = allElements.find((e) => e.id === id);
			return el ? { element: el, value: ELEMENTAL_ATTACK_MODIFIER } : null;
		})
		.filter((r): r is Relation => r !== null);
}

/**
 * Mapea debilidades de un ataque a elementos completos con value fijo = 20
 */
export function getAttackWeaknesses(
	allElements: Element[],
	element: Element | null,
): Relation[] {
	if (!element || !Array.isArray(element.weaknesses)) return [];

	return element.weaknesses
		.map((id) => {
			const el = allElements.find((e) => e.id === id);
			return el ? { element: el, value: ELEMENTAL_ATTACK_MODIFIER } : null;
		})
		.filter((r): r is Relation => r !== null);
}
