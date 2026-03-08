import type { ClientCard, Zone } from '../game/models';

const DEV_OWNER_ID = 'dev-tool';

let _nextIndex = 0;

export function createDummyCard(zone: Zone = 'DECK'): ClientCard {
	const i = _nextIndex++;
	return {
		instanceId: `dev_card_${i}`,
		cardId: i,
		ownerId: DEV_OWNER_ID,
		name: `Test Card ${i}`,
		zone,
		currentHealth: 10,
		maxHealth: 10,
		physicalDefence: 5,
		magicDefence: 5,
		isAlive: true,
		faceUp: false,
	};
}

export function resetDummyCardIndex(): void {
	_nextIndex = 0;
}
