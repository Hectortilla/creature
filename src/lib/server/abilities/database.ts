import db from '$lib/server/db.js';
import { formatHandle } from '$lib/utils/formatHandle';
import type { Ability, CreateAbility } from '$lib/types';

// Get all attacks
export function getAllAbilities(): (Ability)[] {
	return db.prepare('SELECT * FROM abilities').all() as Ability[];
}


export function getAbility(value: string | number): Ability | null {
    let ability: Ability | undefined;

    if (!isNaN(Number(value))) {
        ability = db.prepare('SELECT * FROM abilities WHERE code = ?').get(Number(value)) as Ability | undefined;
    } else {
        ability = db.prepare('SELECT * FROM abilities WHERE name = ? COLLATE NOCASE').get(value) as Ability | undefined;
    }

    return ability ? ability : null;
}


// Create Ability
export function createAbility({
		created_at,
		code,
		name,
		description,
		type,
	}: CreateAbility): Ability {
		const handle = formatHandle(name);
		const stmt = db.prepare(`
			INSERT INTO abilities (
				created_at, code, name, handle, description, type
			) VALUES (?, ?, ?, ?, ?, ?)
		`);
		const result = stmt.run(
			created_at,
			code,
			name,
			handle,
			description,
			type
		);

		return {
			id: result.lastInsertRowid,
			created_at,
			code,
			name,
			handle,
			description,
			type
		};
}

export function deleteAbility(id:number) {
	const stmt = db.prepare('DELETE FROM abilities WHERE id = ?');
	const result = stmt.run(id);
	return result.changes > 0;
}

