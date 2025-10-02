export interface Creature {
  id: number | bigint;
  created_at: string;
  code: number;
  name: string;
  is_evolution: any;
  next_evolution: any;
  handle: string;
  description: string;
  image: string | null;
  overlay_image: string | null;
  first_element: any;
  second_element: any;
  type: any;
  character: any;
  first_attack: any;
  second_attack: any;
  health: number;
  physical_defence: number;
  magic_defence: number;
  forces: any;
  ability: any;
  association: any;
  weaknesses: any;
  strengths: any;
}

export type CreateCreature = Omit<Creature, 'id' | 'handle'>;

export interface CardCreature {
  code: number;
  name: string;
  is_evolution: any;
  handle: string;
  image: string | null;
  overlay_image: string | null;
  first_element: any;
  second_element: any;
  type: any;
  character: any;
}

export interface Attack {
    id: number | bigint;
    code: number;
    created_at: string;
    name: string;
    handle: string;
    description: string;
    damage: number;
    type: string;
    element: any;
    dice_rolls: number;
    necessary_force: any;
    effect: string | null;
    strengths: any;
    weaknesses: any;
}

export type CreateAttack = Omit<Attack, 'id' | 'handle'>;

export interface Ability {
    id: number | bigint;
    code: number;
    created_at: string;
    name: string;
    handle: string;
    description: string;
    type: string;
}

export type CreateAbility = Omit<Ability, 'id' | 'handle'>;

export interface Association {
    id: number | bigint;
    code: number;
    created_at: string;
    name: string;
    handle: string;
    description: string;
}

export type CreateAssociation = Omit<Association, 'id' | 'handle'>;

export interface Element {
    id: number | bigint;
    label: string;
    icon: string;
    strengths: any;
    weaknesses: any;
    color: string;
}

export interface Type {
    id: number | bigint;
    label: string;
    icon: string;
}

export interface Character {
    id: number | bigint;
    label: string;
    icon: string;
}