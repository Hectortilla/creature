import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type { GameStateStore, TurnChangedData } from '../state/GameStateStore';

const FADE_IN_MS = 200;
const HOLD_MS = 1000;
const FADE_OUT_MS = 400;

const MY_TURN_COLOR = '#4CAF50';
const OPP_TURN_COLOR = '#F44336';
const BACKDROP_COLOR = 'rgba(0, 0, 0, 0.5)';

export class TurnBanner {
	private _backdrop: Rectangle;
	private _text: TextBlock;
	private _stateStore: GameStateStore;
	private _animTimer: ReturnType<typeof setTimeout> | null = null;
	private _animFrame: ReturnType<typeof requestAnimationFrame> | null = null;

	constructor(gui: AdvancedDynamicTexture, stateStore: GameStateStore) {
		this._stateStore = stateStore;

		this._backdrop = new Rectangle('turnBanner_backdrop');
		this._backdrop.width = '500px';
		this._backdrop.height = '100px';
		this._backdrop.cornerRadius = 12;
		this._backdrop.thickness = 0;
		this._backdrop.background = BACKDROP_COLOR;
		this._backdrop.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_CENTER;
		this._backdrop.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_CENTER;
		this._backdrop.alpha = 0;
		this._backdrop.isPointerBlocker = false;
		gui.addControl(this._backdrop);

		this._text = new TextBlock('turnBanner_text', '');
		this._text.fontSize = 42;
		this._text.fontWeight = 'bold';
		this._text.color = '#FFFFFF';
		this._text.isPointerBlocker = false;
		this._backdrop.addControl(this._text);

		stateStore.on('turnChanged', this._onTurnChanged);
	}

	private _onTurnChanged = (data: TurnChangedData): void => {
		const isMyTurn = data.playerId === this._stateStore.myPlayerId;
		this._show(isMyTurn ? 'YOUR TURN' : "OPPONENT'S TURN", isMyTurn ? MY_TURN_COLOR : OPP_TURN_COLOR);
	};

	private _show(message: string, accentColor: string): void {
		this._cancelAnimation();
		this._text.text = message;
		this._text.color = accentColor;
		this._fadeIn();
	}

	private _fadeIn(): void {
		const start = performance.now();
		const step = () => {
			const elapsed = performance.now() - start;
			const t = Math.min(elapsed / FADE_IN_MS, 1);
			this._backdrop.alpha = t;
			if (t < 1) {
				this._animFrame = requestAnimationFrame(step);
			} else {
				this._animTimer = setTimeout(() => this._fadeOut(), HOLD_MS);
			}
		};
		this._animFrame = requestAnimationFrame(step);
	}

	private _fadeOut(): void {
		const start = performance.now();
		const step = () => {
			const elapsed = performance.now() - start;
			const t = Math.min(elapsed / FADE_OUT_MS, 1);
			this._backdrop.alpha = 1 - t;
			if (t < 1) {
				this._animFrame = requestAnimationFrame(step);
			}
		};
		this._animFrame = requestAnimationFrame(step);
	}

	private _cancelAnimation(): void {
		if (this._animTimer !== null) {
			clearTimeout(this._animTimer);
			this._animTimer = null;
		}
		if (this._animFrame !== null) {
			cancelAnimationFrame(this._animFrame);
			this._animFrame = null;
		}
	}

	dispose(): void {
		this._cancelAnimation();
		this._stateStore.off('turnChanged', this._onTurnChanged);
		this._backdrop.dispose();
	}
}
