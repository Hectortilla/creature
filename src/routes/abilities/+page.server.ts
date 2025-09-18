import type { PageServerLoad } from './$types';
import * as abilitiesDB from '$lib/server/abilities/database';


export const load: PageServerLoad = async () => {
	const abilities = abilitiesDB.getAllAbilities();

	return {
		abilities,
	};
};