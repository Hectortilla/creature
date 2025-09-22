// @ts-nocheck
import type { PageServerLoad } from './$types';
import * as cardsDB from '$lib/server/cards/database';
import * as elementsDB from '$lib/server/elements/database';

export const load = async ({ params }: Parameters<PageServerLoad>[0]) => {
    const { card } = params;

    if (!card) {
        throw new Error("Card parameter is missing");
    }

    const cards = cardsDB.getCard(card);
    const variants = cards.flatMap(v => cardsDB.getCard(v.handle));
    const elements = elementsDB.getAllElements();

    return {
        params,
        cards,
        variants,
        elements
    };

};
