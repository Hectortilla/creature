import type { Mesh } from '@babylonjs/core/Meshes/mesh';
import { Color3 } from '@babylonjs/core/Maths/math.color';
import { CardVisualState, type ClientCard, type Zone } from '../game/models';

const HOVER_OUTLINE_WIDTH = 0.02;
const HOVER_OUTLINE_COLOR = new Color3(0.8, 0.8, 0.2);
const SELECTED_OUTLINE_WIDTH = 0.04;
const SELECTED_OUTLINE_COLOR = new Color3(0.2, 0.8, 1.0);
const DISABLED_VISIBILITY = 0.4;
const DRAGGING_VISIBILITY = 0.7;

export class CardEntity {
	readonly instanceId: string;
	private _mesh: Mesh;
	private _cardData: ClientCard;
	private _visualState: CardVisualState = CardVisualState.IDLE;

	constructor(instanceId: string, mesh: Mesh, cardData: ClientCard) {
		this.instanceId = instanceId;
		this._mesh = mesh;
		this._cardData = cardData;
	}

	get mesh(): Mesh {
		return this._mesh;
	}

	set mesh(mesh: Mesh) {
		this._mesh = mesh;
	}

	get cardData(): ClientCard {
		return this._cardData;
	}

	get visualState(): CardVisualState {
		return this._visualState;
	}

	get ownerId(): string {
		return this._cardData.ownerId;
	}

	get zone(): Zone {
		return this._cardData.zone;
	}

	get isAlive(): boolean {
		return this._cardData.isAlive;
	}

	updateCardData(data: Partial<ClientCard>): void {
		Object.assign(this._cardData, data);
	}

	setVisualState(state: CardVisualState): void {
		if (this._visualState === state) return;
		this._visualState = state;
		this.applyVisualState();
	}

	applyVisualState(): void {
		this._resetVisuals();

		switch (this._visualState) {
			case CardVisualState.HOVERED:
				this._mesh.renderOutline = true;
				this._mesh.outlineColor = HOVER_OUTLINE_COLOR;
				this._mesh.outlineWidth = HOVER_OUTLINE_WIDTH;
				break;

			case CardVisualState.SELECTED:
				this._mesh.renderOutline = true;
				this._mesh.outlineColor = SELECTED_OUTLINE_COLOR;
				this._mesh.outlineWidth = SELECTED_OUTLINE_WIDTH;
				break;

			case CardVisualState.DISABLED:
				this._mesh.visibility = DISABLED_VISIBILITY;
				break;

			case CardVisualState.DRAGGING:
				this._mesh.visibility = DRAGGING_VISIBILITY;
				break;

			case CardVisualState.IDLE:
			case CardVisualState.ANIMATING:
				break;
		}
	}

	dispose(): void {
		this._resetVisuals();
		this._mesh.dispose();
	}

	private _resetVisuals(): void {
		this._mesh.renderOutline = false;
		this._mesh.outlineColor = Color3.Black();
		this._mesh.outlineWidth = 0;
		this._mesh.visibility = 1;
	}
}
