import type { PageServerLoad } from './$types';
import {
	getAllAttacksAttacksGet,
	getAllElementsElementsGet
} from '$lib/api';

export const load: PageServerLoad = async () => {
	const [attacksRes, elementsRes] = await Promise.all([
		getAllAttacksAttacksGet(),
		getAllElementsElementsGet()
	]);

	return {
		attacks: attacksRes.data ?? [],
		elements: elementsRes.data ?? []
	};
};
