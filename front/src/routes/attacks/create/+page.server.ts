import type { PageServerLoad } from './$types';
import * as attacksDB from '$lib/server/attacks/database';
import * as elementsDB from '$lib/server/elements/database';

export const load: PageServerLoad = async () => {
	const attacks = attacksDB.getAllAttacks();
	const elements = elementsDB.getAllElements();

	return {
		attacks,
		elements,
	};
};