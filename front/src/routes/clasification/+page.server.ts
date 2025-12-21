import type { PageServerLoad } from './$types';
import {
	getAllElementsElementsGet,
	getAllTypesTypesGet,
	getAllCharactersCharactersGet
} from '$lib/api';

export const load: PageServerLoad = async () => {
	const [elementsRes, typesRes, charactersRes] = await Promise.all([
		getAllElementsElementsGet(),
		getAllTypesTypesGet(),
		getAllCharactersCharactersGet()
	]);

	return {
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? []
	};
};
