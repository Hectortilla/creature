import db from '$lib/server/db.js';
import { formatHandle } from '$lib/utils/formatHandle';
import type { Creature, CreateCreature } from '$lib/types';
import * as elementsDB from '$lib/server/elements/database';
import * as typesDB from '$lib/server/types/database';
import * as charactersDB from '$lib/server/characters/database';
import * as attacksDB from '$lib/server/attacks/database';
import * as abilitiesDB from '$lib/server/abilities/database';
import * as associationsDB from '$lib/server/associations/database';

// Función para enriquecer un ataque con su elemento
function enrichCard(c: Creature, visited = new Set<number>()): Creature {
	if (visited.has(c.code)) return c;
	visited.add(c.code);

	// Enriquecer la carta con todos los campos necesarios
	const enriched: Creature = {
		...c,
		first_element: c.first_element ? elementsDB.getElement(c.first_element) : null,
		second_element: c.second_element ? elementsDB.getElement(c.second_element) : null,
		type: c.type ? typesDB.getType(c.type) : null,
		character: c.character ? charactersDB.getCharacter(c.character) : null,
		first_attack: c.first_attack ? attacksDB.getAttack(c.first_attack) : null,
		second_attack: c.second_attack ? attacksDB.getAttack(c.second_attack) : null,
		ability: c.ability ? abilitiesDB.getAbility(c.ability) : null,
		association: c.association ? associationsDB.getAssociation(c.association) : null,
		forces: c.forces ? JSON.parse(c.forces) : null,
		is_evolution: null,
		next_evolution: null,
	};

	// Enriquecer is_evolution si existe
	if (c.is_evolution) {
		const prevCard = db.prepare('SELECT * FROM cards WHERE code = ?').get(Number(c.is_evolution)) as Creature;
		if (prevCard) {
			enriched.is_evolution = enrichCard(prevCard, visited); // recursivo
		}
	}

	// Enriquecer next_evolution recursivamente
	let nextEvos: Creature[] = [];
	if (c.next_evolution) {
		const codes = String(c.next_evolution).split(',').map(Number).filter(Boolean);
		for (const code of codes) {
			const nextCard = db.prepare('SELECT * FROM cards WHERE code = ?').get(code) as Creature;
			if (nextCard) {
				nextEvos.push(enrichCard(nextCard, visited));
			}
		}
	} else {
		// Buscar cartas que evolucionan desde esta
		const related = db.prepare('SELECT * FROM cards WHERE is_evolution = ?').all(c.code) as Creature[];
		nextEvos = related.map(rc => enrichCard(rc, visited));
	}
	enriched.next_evolution = nextEvos.length > 0 ? nextEvos : null;

	return enriched;
}


// Get all Cards
export function getAllCards() {
	const cards = db.prepare('SELECT * FROM cards').all() as Creature[];
	return cards.map(card => enrichCard(card, new Set<number>()));
}

// Get one Card by NAME or CODE
export function getCard(value: string | number): Creature[] {
    let cards: Creature[];

    if (!isNaN(Number(value))) {
        cards = db.prepare('SELECT * FROM cards WHERE code = ?').all(Number(value)) as Creature[];
    } else {
        cards = db.prepare(
			'SELECT * FROM cards WHERE handle = ? COLLATE NOCASE OR name = ? COLLATE NOCASE'
		).all(value, value) as Creature[];
    }

    return cards.map(card => enrichCard(card, new Set<number>()));
}


// Create Card
export function createCard({
		created_at,
		code,
		name,
		is_evolution,
		next_evolution,
		description,
		image,
		overlay_image,
		first_element,
		second_element,
		type,
		character,
		first_attack,
  		second_attack,
		health,
		physical_defence,
		magic_defence,
		forces,
		ability,
		association
	}: CreateCreature): Creature {
		const handle = formatHandle(name);
		const stmt = db.prepare(`
			INSERT INTO cards (
				created_at, code, name, is_evolution, next_evolution, handle, description,
				image, overlay_image, first_element, second_element, type, character,
				first_attack, second_attack, health, physical_defence,
				magic_defence, forces, ability, association
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		`);
		const result = stmt.run(
			created_at,
			code,
			name,
			is_evolution,
			next_evolution,
			handle,
			description,
			image,
			overlay_image,
			first_element,
			second_element,
			type,
			character,
			first_attack,
  			second_attack,
			health,
			physical_defence,
			magic_defence,
			forces,
			ability,
			association
		);

		return {
			id: result.lastInsertRowid,
			created_at,
			code,
			name,
			is_evolution,
			next_evolution,
			handle,
			description,
			image,
			overlay_image,
			first_element,
			second_element,
			type,
			character,
			first_attack,
  			second_attack,
			health,
			physical_defence,
			magic_defence,
			forces,
			ability,
			association,
		};
}

/**
 * Obtiene todas las cartas que tengan un ataque específico
 * @param attackCode Code del ataque a buscar
 */
export function getCardsByAttack(attackCode: number) {
  const cards = db
    .prepare(`
      SELECT *
      FROM cards
      WHERE first_attack = ? OR second_attack = ?
    `)
    .all(attackCode, attackCode) as Creature[];

  return cards.map(card => enrichCard(card, new Set<number>()));
}

/**
 * Obtiene todas las cartas que tengan una habilidad específica
 * @param abilityCode Code del ataque a buscar
 */
export function getCardsByAbility(abilityCode: number) {
  const cards = db
    .prepare(`
      SELECT *
      FROM cards
      WHERE ability = ?
    `)
    .all(abilityCode) as Creature[];

  return cards.map(card => enrichCard(card, new Set<number>()));
}

/**
 * Obtiene todas las cartas que tengan una asociación específica
 * @param associationCode Code del ataque a buscar
 */
export function getCardsByAssociation(associationCode: number) {
  const cards = db
    .prepare(`
      SELECT *
      FROM cards
      WHERE association = ?
    `)
    .all(associationCode) as Creature[];

  return cards.map(card => enrichCard(card, new Set<number>()));
}

// Delete card
export function deleteCard(id:number) {
	const stmt = db.prepare('DELETE FROM cards WHERE id = ?');
	const result = stmt.run(id);
	return result.changes > 0;
}
