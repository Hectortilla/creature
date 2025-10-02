import type { PageServerLoad } from './$types';
import * as elementsDB from '$lib/server/elements/database';
import * as typesDB from '$lib/server/types/database';
import * as charactersDB from '$lib/server/characters/database';

export const load: PageServerLoad = async () => {
	const elements = elementsDB.getAllElements();
	const types = typesDB.getAllTypes();
	const characters = charactersDB.getAllCharacters();

	return {
		elements,
		types,
		characters
	};
};