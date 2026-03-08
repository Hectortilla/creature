import { Rectangle } from '@babylonjs/gui/2D/controls/rectangle';
import { TextBlock } from '@babylonjs/gui/2D/controls/textBlock';
import { StackPanel } from '@babylonjs/gui/2D/controls/stackPanel';
import type { AdvancedDynamicTexture } from '@babylonjs/gui/2D/advancedDynamicTexture';
import type { TurnPhase } from '../game/models';
import type { GameStateStore, PhaseChangedData, TurnChangedData } from '../state/GameStateStore';

const PHASES: TurnPhase[] = [
	'DRAW' as TurnPhase,
	'PLACEMENT' as TurnPhase,
	'PROMOTION' as TurnPhase,
	'SWAP' as TurnPhase,
	'ASSOCIATION' as TurnPhase,
	'EVOLUTION' as TurnPhase,
	'ATTACK' as TurnPhase,
];

const PHASE_LABELS: Record<string, string> = {
	DRAW: 'Draw',
	PLACEMENT: 'Place',
	PROMOTION: 'Promote',
	SWAP: 'Swap',
	ASSOCIATION: 'Assoc',
	EVOLUTION: 'Evolve',
	ATTACK: 'Attack',
};

const BG_COLOR = 'rgba(15, 10, 40, 0.7)';
const ACTIVE_COLOR = '#D4AF37';
const PASSED_COLOR = 'rgba(255, 255, 255, 0.15)';
const FUTURE_COLOR = 'rgba(255, 255, 255, 0.35)';
const TEXT_COLOR_ACTIVE = '#FFFFFF';
const TEXT_COLOR_DIM = 'rgba(255, 255, 255, 0.5)';

export class PhaseIndicator {
	private _root: Rectangle;
	private _phaseBoxes: Rectangle[] = [];
	private _phaseLabels: TextBlock[] = [];
	private _turnLabel: TextBlock;
	private _stateStore: GameStateStore;
	private _currentIndex = 0;

	constructor(gui: AdvancedDynamicTexture, stateStore: GameStateStore) {
		this._stateStore = stateStore;

		this._root = new Rectangle('phaseIndicator_root');
		this._root.width = '620px';
		this._root.height = '50px';
		this._root.top = '10px';
		this._root.verticalAlignment = Rectangle.VERTICAL_ALIGNMENT_TOP;
		this._root.horizontalAlignment = Rectangle.HORIZONTAL_ALIGNMENT_CENTER;
		this._root.background = BG_COLOR;
		this._root.cornerRadius = 8;
		this._root.thickness = 0;
		this._root.isPointerBlocker = false;
		gui.addControl(this._root);

		const row = new StackPanel('phaseIndicator_row');
		row.isVertical = false;
		row.height = '36px';
		row.isPointerBlocker = false;
		this._root.addControl(row);

		this._turnLabel = new TextBlock('phaseIndicator_turn', 'Your Turn');
		this._turnLabel.width = '90px';
		this._turnLabel.fontSize = 11;
		this._turnLabel.color = ACTIVE_COLOR;
		this._turnLabel.textHorizontalAlignment = TextBlock.HORIZONTAL_ALIGNMENT_CENTER;
		this._turnLabel.isPointerBlocker = false;
		row.addControl(this._turnLabel);

		for (const phase of PHASES) {
			const box = new Rectangle(`phase_${phase}`);
			box.width = '70px';
			box.height = '30px';
			box.cornerRadius = 4;
			box.thickness = 0;
			box.background = FUTURE_COLOR;
			box.isPointerBlocker = false;
			box.paddingLeft = '2px';
			box.paddingRight = '2px';

			const label = new TextBlock(`phaseLabel_${phase}`, PHASE_LABELS[phase as string] ?? (phase as string));
			label.fontSize = 11;
			label.color = TEXT_COLOR_DIM;
			label.isPointerBlocker = false;
			box.addControl(label);

			row.addControl(box);
			this._phaseBoxes.push(box);
			this._phaseLabels.push(label);
		}

		stateStore.on('phaseChanged', this._onPhaseChanged);
		stateStore.on('turnChanged', this._onTurnChanged);

		const initial = stateStore.currentPhase;
		if (initial) this._applyPhase(initial);
		this._applyTurnLabel(stateStore.isMyTurn);
	}

	private _onPhaseChanged = (data: PhaseChangedData): void => {
		this._applyPhase(data.toPhase);
	};

	private _onTurnChanged = (data: TurnChangedData): void => {
		this._applyTurnLabel(data.playerId === this._stateStore.myPlayerId);
		this._currentIndex = 0;
		this._refreshBoxes();
	};

	private _applyPhase(phase: TurnPhase): void {
		const idx = PHASES.indexOf(phase);
		if (idx === -1) return;
		this._currentIndex = idx;
		this._refreshBoxes();
	}

	private _refreshBoxes(): void {
		for (let i = 0; i < PHASES.length; i++) {
			const box = this._phaseBoxes[i];
			const label = this._phaseLabels[i];
			if (i < this._currentIndex) {
				box.background = PASSED_COLOR;
				label.color = TEXT_COLOR_DIM;
			} else if (i === this._currentIndex) {
				box.background = ACTIVE_COLOR;
				label.color = TEXT_COLOR_ACTIVE;
			} else {
				box.background = FUTURE_COLOR;
				label.color = TEXT_COLOR_DIM;
			}
		}
	}

	private _applyTurnLabel(isMyTurn: boolean): void {
		this._turnLabel.text = isMyTurn ? 'Your Turn' : "Opp's Turn";
		this._turnLabel.color = isMyTurn ? ACTIVE_COLOR : 'rgba(255, 100, 100, 0.9)';
	}

	dispose(): void {
		this._stateStore.off('phaseChanged', this._onPhaseChanged);
		this._stateStore.off('turnChanged', this._onTurnChanged);
		this._root.dispose();
	}
}
