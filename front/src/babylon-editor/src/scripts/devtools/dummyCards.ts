import type { ClientCard, Zone } from '../game/models';

const DEV_OWNER_ID = 'dev-tool';

let _nextIndex = 0;

export function createDummyCard(zone: Zone = 'DECK'): ClientCard {
	const i = _nextIndex++;
	return {
		instance_id: `dev_card_${i}`,
		card_id: i,
		owner_id: DEV_OWNER_ID,
		name: `Test Card ${i}`,
		zone,
		current_health: 10,
		health: 10,
		physical_defence: 5,
		magic_defence: 5,
		is_alive: true,
		faceUp: false,
		can_attack: false,
		can_promote: false,
		can_evolve: false,
	};
}

export function resetDummyCardIndex(): void {
	_nextIndex = 0;
}
