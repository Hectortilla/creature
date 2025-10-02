import type { PageServerLoad } from './$types';
import * as cardsDB from '$lib/server/cards/database';
import * as elementsDB from '$lib/server/elements/database';
import * as typesDB from '$lib/server/types/database';
import * as charactersDB from '$lib/server/characters/database';

export const load: PageServerLoad = async () => {
    const cards = cardsDB.getAllCards();
    const elements = elementsDB.getAllElements();
    const types = typesDB.getAllTypes();
    const characters = charactersDB.getAllCharacters();

    return {
        cards,
        elements,
        types,
        characters
    };
};
