// @ts-nocheck
import type { PageServerLoad } from './$types';
import * as cardsDB from '$lib/server/cards/database';
import * as elementsDB from '$lib/server/elements/database';
import * as typesDB from '$lib/server/types/database';
import * as charactersDB from '$lib/server/characters/database';
import * as attacksDB from '$lib/server/attacks/database';
import * as abilitiesDB from '$lib/server/abilities/database';
import * as associationsDB from '$lib/server/associations/database';

export const load = async () => {
	const cards = cardsDB.getAllCards();
        const elements = elementsDB.getAllElements();
        const types = typesDB.getAllTypes();
        const characters = charactersDB.getAllCharacters();
        const attacks = attacksDB.getAllAttacks();
		const abilities = abilitiesDB.getAllAbilities();
		const associations = associationsDB.getAllAssociations();

	return {
		cards,
		elements,
		types,
		characters,
        attacks,
		abilities,
		associations
	};
};;null as any as PageServerLoad;