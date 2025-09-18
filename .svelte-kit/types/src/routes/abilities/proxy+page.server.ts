// @ts-nocheck
import type { PageServerLoad } from './$types';
import * as abilitiesDB from '$lib/server/abilities/database';


export const load = async () => {
	const abilities = abilitiesDB.getAllAbilities();

	return {
		abilities,
	};
};;null as any as PageServerLoad;