import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type { Zone } from '../game/models';
import type { CardEntity } from '../entities/CardEntity';
import type { CardEntityManager } from '../entities/CardEntityManager';
import type {
	GameStateStore,
	CardHealthChangedData,
	CardMovedData,
	CardDestroyedData,
} from '../state/GameStateStore';

const BAR_WIDTH = 60;
const BAR_HEIGHT = 10;
const LINK_OFFSET_Y = -50;
const BG_COLOR = 'rgba(0, 0, 0, 0.6)';

const FIELD_ZONES: Zone[] = ['SUPPORTING' as Zone, 'ATTACKING' as Zone];

function healthColor(ratio: number): string {
	if (ratio > 0.6) return '#4CAF50';
	if (ratio > 0.3) return '#FFC107';
	return '#F44336';
}

// ============================================================================
// Single health bar attached to one card mesh
// ============================================================================

class HealthBar {
	private _container: Rectangle;
	private _fill: Rectangle;
	private _label: TextBlock;

	constructor(gui: AdvancedDynamicTexture, entity: CardEntity) {
		const id = entity.instanceId;
		this._container = new Rectangle(`hb_${id}`);
		this._container.width = `${BAR_WIDTH}px`;
		this._container.height = `${BAR_HEIGHT + 6}px`;
		this._container.cornerRadius = 4;
		this._container.thickness = 0;
		this._container.background = BG_COLOR;
		this._container.isPointerBlocker = false;
		gui.addControl(this._container);
		this._container.linkWithMesh(entity.mesh);
		this._container.linkOffsetY = LINK_OFFSET_Y;

		this._fill = new Rectangle(`hb_fill_${id}`);
		this._fill.width = '100%';
		this._fill.height = `${BAR_HEIGHT}px`;
		this._fill.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_LEFT;
		this._fill.thickness = 0;
		this._fill.cornerRadius = 3;
		this._fill.isPointerBlocker = false;
		this._container.addControl(this._fill);

		this._label = new TextBlock(`hb_label_${id}`, '');
		this._label.fontSize = 8;
		this._label.color = '#FFFFFF';
		this._label.isPointerBlocker = false;
		this._container.addControl(this._label);

		this.updateHealth(entity.cardData.currentHealth, entity.cardData.maxHealth);
	}

	updateHealth(current: number, max: number): void {
		const ratio = max > 0 ? Math.max(0, current / max) : 0;
		this._fill.width = `${Math.round(ratio * 100)}%`;
		this._fill.background = healthColor(ratio);
		this._label.text = `${current}/${max}`;
	}

	dispose(): void {
		this._container.dispose();
	}
}

// ============================================================================
// Manager that tracks health bars for all field cards
// ============================================================================

export class HealthBarManager {
	private _gui: AdvancedDynamicTexture;
	private _stateStore: GameStateStore;
	private _cardManager: CardEntityManager;
	private _bars = new Map<string, HealthBar>();

	constructor(gui: AdvancedDynamicTexture, stateStore: GameStateStore, cardManager: CardEntityManager) {
		this._gui = gui;
		this._stateStore = stateStore;
		this._cardManager = cardManager;

		stateStore.on('cardMoved', this._onCardMoved);
		stateStore.on('cardHealthChanged', this._onHealthChanged);
		stateStore.on('cardDestroyed', this._onCardDestroyed);
	}

	private _isFieldZone(zone: Zone): boolean {
		return FIELD_ZONES.includes(zone);
	}

	private _onCardMoved = (data: CardMovedData): void => {
		const enteringField = this._isFieldZone(data.toZone);
		const leavingField = this._isFieldZone(data.fromZone);

		if (enteringField && !this._bars.has(data.instanceId)) {
			const entity = this._cardManager.getByInstanceId(data.instanceId);
			if (entity) {
				this._bars.set(data.instanceId, new HealthBar(this._gui, entity));
			}
		}

		if (leavingField && !enteringField) {
			this._removeBar(data.instanceId);
		}
	};

	private _onHealthChanged = (data: CardHealthChangedData): void => {
		this._bars.get(data.instanceId)?.updateHealth(data.newHealth, data.maxHealth);
	};

	private _onCardDestroyed = (data: CardDestroyedData): void => {
		this._removeBar(data.instanceId);
	};

	private _removeBar(instanceId: string): void {
		const bar = this._bars.get(instanceId);
		if (!bar) return;
		bar.dispose();
		this._bars.delete(instanceId);
	}

	dispose(): void {
		this._stateStore.off('cardMoved', this._onCardMoved);
		this._stateStore.off('cardHealthChanged', this._onHealthChanged);
		this._stateStore.off('cardDestroyed', this._onCardDestroyed);
		for (const bar of this._bars.values()) bar.dispose();
		this._bars.clear();
	}
}
