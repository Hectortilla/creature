// @ts-nocheck
import type { PageServerLoad } from './$types';
import * as associationsDB from '$lib/server/associations/database';
import * as cardsDB from '$lib/server/cards/database';

export const load = async ({ params }: Parameters<PageServerLoad>[0]) => {
    const { association } = params;

    if (!association) {
        throw new Error("Ability parameter is missing");
    }


    let data: Record<string, unknown> = {};
	data.association = associationsDB.getAssociation(association);
    data.cards_use_association = cardsDB.getCardsByAssociation(Number(association));

	return { params, ...data };
};