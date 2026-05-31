import { describe, expect, it } from "vitest";
import type { Element } from "$lib/types";
import { ELEMENTAL_ATTACK_MODIFIER } from "$lib/constants";
import {
	getCardStrengths,
	getCardWeaknesses,
} from "./getStrenghtsAndWeaknesses";

/**
 * Exemplar unit test for pure domain logic that depends only on types +
 * constants (no SvelteKit runtime, no network, no Babylon). New rule-logic
 * tests should follow this shape: build minimal fixtures, assert the derived
 * relations.
 */

// Minimal element fixtures. `strengths`/`weaknesses` hold the ids of the
// elements an element is strong/weak *against*.
const fire: Element = { id: 1, label: "Fire", strengths: [3], weaknesses: [2] }; // strong vs Nature, weak vs Water
const water: Element = {
	id: 2,
	label: "Water",
	strengths: [1],
	weaknesses: [3],
}; // strong vs Fire, weak vs Nature
const nature: Element = {
	id: 3,
	label: "Nature",
	strengths: [2],
	weaknesses: [1],
}; // strong vs Water, weak vs Fire

const all: Element[] = [fire, water, nature];

describe("getCardStrengths", () => {
	it("returns attack elements the card has advantage against, with positive magnitude", () => {
		// A Fire card: Nature is weak vs Fire -> Fire card is strong against Nature attacks.
		const strengths = getCardStrengths(all, fire);
		expect(strengths).toEqual([
			{ element: nature, value: ELEMENTAL_ATTACK_MODIFIER },
		]);
	});

	it("returns an empty array when no card element is provided", () => {
		expect(getCardStrengths(all, null, null)).toEqual([]);
	});
});

describe("getCardWeaknesses", () => {
	it("returns attack elements the card is at a disadvantage against, as positive magnitude", () => {
		// A Fire card: Water is strong vs Fire -> Fire card is weak against Water attacks.
		const weaknesses = getCardWeaknesses(all, fire);
		expect(weaknesses).toEqual([
			{ element: water, value: ELEMENTAL_ATTACK_MODIFIER },
		]);
	});

	it("ignores the card element itself when computing relations", () => {
		const weaknesses = getCardWeaknesses(all, fire);
		expect(weaknesses.some((r) => r.element.id === fire.id)).toBe(false);
	});
});
