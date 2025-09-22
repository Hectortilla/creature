import db from '$lib/server/db.js';
import { formatHandle } from '$lib/utils/formatHandle';
import { getAttackStrengths, getAttackWeaknesses } from '$lib/utils/getStrenghtsAndWeaknesses';
import type { Attack, CreateAttack } from '$lib/types';
import * as elementsDB from '$lib/server/elements/database';

// Función para enriquecer un ataque con su elemento
function enrichAttack(a: Attack): Attack {
    return {
        ...a,
        element: a.element ? elementsDB.getElement(a.element) : null,
		necessary_force: a.necessary_force ? JSON.parse(a.necessary_force) : null,
		strengths: getAttackStrengths(
			elementsDB.getAllElements(),
			elementsDB.getElement(a.element) ?? null
		),
		weaknesses: getAttackWeaknesses(
			elementsDB.getAllElements(),
			elementsDB.getElement(a.element) ?? null
		),
    };
}

// Get all attacks
export function getAllAttacks(): (Attack & { elementData?: Element })[] {
	const attacks = db.prepare('SELECT * FROM attacks').all() as Attack[];
	return attacks.map(enrichAttack);
}


export function getAttack(value: string | number): Attack | null {
    let attack: Attack | undefined;

    if (!isNaN(Number(value))) {
        attack = db.prepare('SELECT * FROM attacks WHERE code = ?').get(Number(value)) as Attack | undefined;
    } else {
        attack = db.prepare('SELECT * FROM attacks WHERE name = ? COLLATE NOCASE').get(value) as Attack | undefined;
    }

    return attack ? enrichAttack(attack) : null;
}


// Create Attack
export function createAttack({
		created_at,
		code,
		name,
		description,
		element,
		type,
		damage,
		dice_rolls,
		necessary_force,
		effect,
		strengths,
		weaknesses
	}: CreateAttack): Attack {
		const handle = formatHandle(name);
		const stmt = db.prepare(`
			INSERT INTO attacks (
				created_at, code, name, handle, description,
				element, type, damage, dice_rolls, necessary_force, effect, strengths, weaknesses
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		`);
		const result = stmt.run(
			created_at,
			code,
			name,
			handle,
			description,
			element,
			type,
			damage,
			dice_rolls,
			necessary_force,
			effect,
			strengths,
			weaknesses,
		);

		return {
			id: result.lastInsertRowid,
			created_at,
			code,
			name,
			handle,
			description,
			element,
			type,
			damage,
			dice_rolls,
			necessary_force,
			effect,
			strengths: null,
			weaknesses: null,
		};
}

export function deleteAttack(id:number) {
	const stmt = db.prepare('DELETE FROM attacks WHERE id = ?');
	const result = stmt.run(id);
	return result.changes > 0;
}

