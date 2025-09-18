import db from '$lib/server/db.js';

export function getAllTypes() {
	return db.prepare('SELECT * FROM types').all();
}

export function getType(value:string | number) {
	if (!isNaN(Number(value))) {
		return db.prepare('SELECT * FROM types WHERE id = ?').get(Number(value));
	}
	else {
		return db.prepare('SELECT * FROM types WHERE label = ?').get(value);
	}
}