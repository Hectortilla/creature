# Game Rules Specification

## 1. General Overview

* This is a **two-player** turn-based card game.
* Each player has identical zone structures and follows the same turn sequence.
* The game uses **creature cards only**.
* Combat are driven by **Elements** (similar to mana types).

---

## 2. Zones (Per Player)

Each player has **5 zones**:

### 2.1 Deck

* Contains **22 cards** at the start of the game.
* Cards are drawn from here into the hand.

### 2.2 Hand

* Contains cards drawn from the deck.
* Cards can be played from the hand into other zones, depending on rules.

### 2.3 Graveyard

* Destroyed creatures are placed here.
* Cards in the graveyard have no effect.

### 2.4 Active Board Zones

There are **two active zones** on the board:

#### 2.4.1 Supporting Zone

* Maximum capacity: **3 cards**
* Cards here:

  * Cannot attack
  * Contribute:

    * Their **elements**
    * Their **skills**
* Cards can be placed here directly from the hand.
* A card must stay here for **at least one full turn** before moving to the attacking zone.
* Cards here may be swapped with attacking cards.

#### 2.4.2 Attacking Zone

* Maximum capacity: **2 cards**
* Cards here:

  * Can attack
  * Contribute:

    * Their **elements**
    * Their **skills**
* Cards can only enter this zone from the supporting zone.

Once placed in any active zone, **cards cannot be removed voluntarily**.

---

## 3. Turn Structure

Each player’s turn follows this order:

1. **Draw Phase**

   * Draw exactly **1 card** from the deck.

2. **Placement Phase**

   * Place up to **N cards** from hand into the supporting zone.
   * `N` is limited by available free slots (maximum 3 total).

3. **Promotion Phase**

   * Move up to **N cards** from the supporting zone to the attacking zone.
   * `N` is limited by free attacking slots (maximum 2).
   * Only cards that have spent **at least one full turn** in the supporting zone may be moved.

4. **Swap Phase**

   * During this phase, the player may swap any number of supporting cards with attacking cards, as long as there are valid slots in each zone.
   * During this turn:

     * Neither card contributes **elements** during this turn.
     * Both cards’ **skills remain active**
     * The attacking card may still attack

5. **Association Phase**

   * Apply association cards:

     * From hand or supporting zone
     * To any active creature (support or attack)

6. **Evolution Phase**

   * Apply evolution cards from hand to eligible active creatures.

7. **Attack Phase**

   * Attack with:

     * Zero, one, or both attacking creatures
   * Attacks can only occur if enough elements are available.

---

## 4. Turn Exceptions

### 4.1 First Turn (Game Start)

* Player draws **4 cards** instead of 1.
* Restrictions:

  * Can only place cards in the **supporting zone**
  * Cannot:

    * Attack
    * Associate
    * Evolve cards

### 4.2 Second Turn

* Player can:

  * Place cards in supporting zone
  * Move cards to attacking zone
  * Attack
  * Associate
* Player **cannot evolve cards**

---

## 5. Elements System

* There are **13 Elements**.
* Each creature:

  * Belongs to **1 or more elements**
  * May contribute **0 or more element amounts** when active
* There exists an **Element Interaction Matrix**:

  * Defines bonuses or penalties between attacking element and defending element(s)
  * Multiple target elements are all evaluated and summed

Element contributions are:

* Consumed when attacks are used
* Restored at the start of the player’s next turn

---

## 6. Creature Cards

All cards in the game are **creatures**.

### 6.1 Creature Properties

Each creature has:

* **Life** (HP)
* **Defense values**:

  * Physical Defense
  * Magical Defense
* **Elements** (1 or more)
* **Element Contribution** (0 or more)
* **Attacks** (0 to N)
* **Skills** (0 to N)
* **Associations** (0 to N)
* **Evolution** (True or False)

---

## 7. Attacks

### 7.1 Attack Usage

* Each attacking creature:

  * May perform **one attack per turn**
  * Must choose exactly one of its available attacks
* Each attack:

  * Consumes a defined amount of specific elements
  * Belongs to exactly **one element**
  * Deals either:

    * Physical damage
    * Magical damage
* Attacks always target **one opposing attacking creature**

### 7.2 Damage Calculation

Damage is calculated in the following order:

1. Base damage value defined on the attack
2. Add element interaction bonus/penalty:

   * From the element interaction matrix
   * Calculated for **each combination** of:

     * Attack element
     * Target creature elements
3. Add any card-specific damage modifiers per target element
4. Subtract the target’s corresponding defense type
5. Final result:

   * If positive → damage dealt to target’s life
   * If negative → damage dealt to attacker’s life

Damage is permanently subtracted from life.

### 7.3 Destruction

* If a creature’s life reaches **0** or below:

  * It is destroyed
  * Moved to the graveyard
  * Frees its attacking slot

### 7.4 Special Effects

* Attacks may have optional **special effects**
* These effects always trigger when the attack is used

---

## 8. No Defenders Rule

* If a player has **no attacking creatures** and is attacked:

  * The game pauses
  * The defending player must move one supporting creature to the attacking zone to receive damage
* If the defending player has **no supporting creatures**:

  * That player **loses the game immediately**

---

## 9. Skills

* Skills are **passive effects**
* All skills of creatures in active zones (support or attack):

  * Are always active
  * Affect the entire game state unless otherwise specified

---

## 10. Associations

* Associations are similar to skills, but:

  * Affect **only one target creature**
* Associations:

  * Are placed underneath the associated creature
  * Can be applied from:

    * Hand
    * Supporting zone
* A creature used as an association:

  * Does not contribute elements
  * Cannot attack
  * Does not occupy an active zone slot
  * Cannot evolve
  * Skills are not activated
  * Cannot be de-associated

---

## 11. Supporting Zone Rules (Summary)

* Supporting creatures:

  * Cannot attack
  * Contribute skills and elements
* Movement rules:

  * Can move to attacking zone only after 1 full turn
  * Can be swapped with attacking creatures
* During swaps:

  * No element contribution from either card for that turn
  * Skills remain active
  * Attacking creature may still attack

---

## 12. Evolutions

* Evolutions are special creature cards
* Evolution rules:

  * Played from hand
  * Must target the creature they evolve from
  * Target creature must:

    * Be in an active zone
    * Have been active for at least 1 full turn
* Evolution replaces the original creature entirely
* Typically results in a stronger version

---

## 13. End Game Condition

* A player **loses the game** if:

  * They are attacked
  * And they have **no active creatures** (attacking or supporting) to defend
