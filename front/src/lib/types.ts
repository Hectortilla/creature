// Re-export types from the generated API client
export type {
  AbilityCreate,
  AbilityRead,
  AssociationCreate,
  AssociationRead,
  AttackCreate,
  AttackReadWithElement,
  CardCreate,
  CardRead,
  CardReadWithRelations,
  CharacterCreate,
  CharacterRead,
  DeckCreate,
  DeckReadWithCards,
  DeckUpdate,
  ElementCreate,
  ElementRead,
  TypeCreate,
  TypeRead,
} from '$lib/api/types.gen';

// Type aliases to match original naming conventions
export type Creature = import('$lib/api/types.gen').CardReadWithRelations;
export type CreateCreature = import('$lib/api/types.gen').CardCreate;
export type CardCreature = import('$lib/api/types.gen').CardReadWithRelations;
export type Attack = import('$lib/api/types.gen').AttackReadWithElement;
export type CreateAttack = import('$lib/api/types.gen').AttackCreate;
export type Ability = import('$lib/api/types.gen').AbilityRead;
export type CreateAbility = import('$lib/api/types.gen').AbilityCreate;
export type Association = import('$lib/api/types.gen').AssociationRead;
export type CreateAssociation = import('$lib/api/types.gen').AssociationCreate;
export type Element = import('$lib/api/types.gen').ElementRead;
export type Type = import('$lib/api/types.gen').TypeRead;
export type Character = import('$lib/api/types.gen').CharacterRead;
