import type { PageServerLoad } from './$types';
import * as abilitiesDB from '$lib/server/abilities/database';
import * as cardsDB from '$lib/server/cards/database';

export const load: PageServerLoad = async ({ params }) => {
    const { ability } = params;

    if (!ability) {
        throw new Error("Ability parameter is missing");
    }


    let data: Record<string, unknown> = {};
	data.ability = abilitiesDB.getAbility(ability);
    data.cards_use_ability = cardsDB.getCardsByAbility(Number(ability));

	return { params, ...data };
};