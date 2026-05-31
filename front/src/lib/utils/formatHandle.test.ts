import { describe, expect, it } from "vitest";
import { formatHandle } from "./formatHandle";

/**
 * Exemplar unit test for a pure util. Copy this shape for new pure-function
 * tests: import the function, assert input -> output, cover the edge cases.
 */
describe("formatHandle", () => {
	it("slugifies spaces and lowercases", () => {
		expect(formatHandle("Fire Dragon")).toBe("fire-dragon");
	});

	it("strips diacritics and non-alphanumeric characters", () => {
		expect(formatHandle("Pokémon!")).toBe("pokemon");
		expect(formatHandle("Águila / Roja")).toBe("aguila--roja");
	});

	it("coerces numbers to strings", () => {
		expect(formatHandle(42)).toBe("42");
	});

	it("returns an empty string for null and undefined", () => {
		expect(formatHandle(null)).toBe("");
		expect(formatHandle(undefined)).toBe("");
	});
});
