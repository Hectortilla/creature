import type { PageLoad } from './$types';

export const load: PageLoad = ({ url }) => {
	const deckId = url.searchParams.get('deck_id');
	const roomId = url.searchParams.get('room_id');
	const createRoom = url.searchParams.get('create_room') === 'true';

	return {
		gameParams: deckId
			? {
					deckId: parseInt(deckId, 10),
					roomId: roomId || null,
					createRoom
				}
			: null
	};
};
