import type { PageServerLoad } from './$types';
import * as associationsDB from '$lib/server/associations/database';


export const load: PageServerLoad = async () => {
	const associations = associationsDB.getAllAssociations();

	return {
		associations,
	};
};