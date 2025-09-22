import db from '$lib/server/db.js';
import type { Element } from '$lib/types';

// Función auxiliar para convertir string de números a array de números
function parseNumberList(value: string | null): number[] | null {
	if (!value) return null;              // null o undefined
	return value
		.split(',')                        // separar por coma
		.map(v => v.trim())                 // quitar espacios por si hay "1, 2"
		.filter(v => v !== '')              // quitar strings vacíos
		.map(Number)                        // convertir a número
		.filter(n => !isNaN(n));           // eliminar valores que no son números
}

// Función para enriquecer un elemento
function enrichElement(e: Element, visited = new Set<number|bigint>()): Element {
	if (visited.has(e.id)) return e;
	visited.add(e.id);

	// Enriquecer la carta con todos los campos necesarios
	const enriched: Element = {
		...e,
		weaknesses: parseNumberList(e.weaknesses),
		strengths: parseNumberList(e.strengths),
	};

	return enriched;
}

export function getAllElements() {
	const elements = db.prepare('SELECT * FROM elements').all() as Element[];
	return elements.map(element => enrichElement(element, new Set<number>()));
}

// Get one Element by NAME or ID
export function getElement(value: string | number): Element | null {
    let element: Element | undefined;

    if (!isNaN(Number(value))) {
        element = db.prepare('SELECT * FROM elements WHERE id = ?').get(Number(value)) as Element | undefined;
    } else {
        element = db.prepare('SELECT * FROM elements WHERE label = ?').get(value) as Element | undefined;
    }

    if (!element) return null;

    return enrichElement(element, new Set<number>());
}