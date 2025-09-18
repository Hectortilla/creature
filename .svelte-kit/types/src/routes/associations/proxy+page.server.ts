// @ts-nocheck
import type { PageServerLoad } from './$types';
import * as associationsDB from '$lib/server/associations/database';


export const load = async () => {
	const associations = associationsDB.getAllAssociations();

	return {
		associations,
	};
};;null as any as PageServerLoad;