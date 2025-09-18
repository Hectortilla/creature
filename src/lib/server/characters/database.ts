import db from '$lib/server/db.js';

export function getAllCharacters() {
	return db.prepare('SELECT * FROM characters').all();
}

export function getCharacter(value:string | number) {
	if (!isNaN(Number(value))) {
		return db.prepare('SELECT * FROM characters WHERE id = ?').get(Number(value));
	}
	else {
		return db.prepare('SELECT * FROM characters WHERE label = ?').get(value);
	}
}