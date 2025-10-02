import db from '$lib/server/db.js';
import { formatHandle } from '$lib/utils/formatHandle';
import type { Association, CreateAssociation } from '$lib/types';

// Get all attacks
export function getAllAssociations(): (Association)[] {
	return db.prepare('SELECT * FROM associations').all() as Association[];
}


export function getAssociation(value: string | number): Association | null {
    let association: Association | undefined;

    if (!isNaN(Number(value))) {
        association = db.prepare('SELECT * FROM associations WHERE code = ?').get(Number(value)) as Association | undefined;
    } else {
        association = db.prepare('SELECT * FROM associations WHERE name = ? COLLATE NOCASE').get(value) as Association | undefined;
    }

    return association ? association : null;
}


// Create Ability
export function createAssociation({
		created_at,
		code,
		name,
		description,
	}: CreateAssociation): Association {
		const handle = formatHandle(name);
		const stmt = db.prepare(`
			INSERT INTO associations (
				created_at, code, name, handle, description
			) VALUES (?, ?, ?, ?, ?)
		`);
		const result = stmt.run(
			created_at,
			code,
			name,
			handle,
			description,
		);

		return {
			id: result.lastInsertRowid,
			created_at,
			code,
			name,
			handle,
			description,
		};
}

export function deleteAssociation(id:number) {
	const stmt = db.prepare('DELETE FROM associations WHERE id = ?');
	const result = stmt.run(id);
	return result.changes > 0;
}

