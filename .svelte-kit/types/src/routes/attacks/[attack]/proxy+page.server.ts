// @ts-nocheck
import type { PageServerLoad } from './$types';
import * as attacksDB from '$lib/server/attacks/database';
import * as cardsDB from '$lib/server/cards/database';

export const load = async ({ params }: Parameters<PageServerLoad>[0]) => {
    const { attack } = params;

    if (!attack) {
        throw new Error("Attack parameter is missing");
    }

    let data: Record<string, unknown> = {};
	data.attack = attacksDB.getAttack(attack);
    data.cards_use_attack = cardsDB.getCardsByAttack(Number(attack));

	return { params, ...data };
};