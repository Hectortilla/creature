import db from '$lib/server/db.js';

export function getAllElements() {
	return db.prepare('SELECT * FROM elements').all();
}

export function getElement(value:string|number) {
	if (!isNaN(Number(value))) {
		return db.prepare('SELECT * FROM elements WHERE id = ?').get(Number(value));
	}
	else {
		return db.prepare('SELECT * FROM elements WHERE label = ?').get(value);
	}
}