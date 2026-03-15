<script lang="ts">
    import type { Attack, Element } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';
    import { changeThemeTo } from '$lib/utils/changeThemeTo';

    // Components
    import InputNumber from "$lib/components/input/Number.svelte";
    import InputText from "$lib/components/input/Text.svelte";
    import RadioList from "$lib/components/input/RadioList.svelte"
    import Divider from "$lib/components/Divider.svelte"
    import Select from "$lib/components/input/Select.svelte"
    import Forces from "$lib/components/input/Forces.svelte"
    import Button from "$lib/components/Button.svelte"

    // Icons
    import diceRollsIcon from "$lib/assets/icons/dice-rolls.svg?raw"

    interface PageProps {
        data: {
            attacks?: Attack[];
            elements: Element[];
        };
    }
    let { data }: PageProps = $props();

    let attacks = $state([...data.attacks ?? []]);
    $inspect("Attacks loaded:", attacks);

    /*
     * Search next code in cards
     * */
    let nextAttackCode = $derived.by(() => {
        if (!attacks || attacks.length === 0) return 1;

        const maxCode = Math.max(...attacks.map(a => a.code ?? 0));
        return maxCode + 1;
    });
    $effect(() => {
        $inspect(nextAttackCode);
    })

    // New Card data
    let attackCode = $derived.by(() => nextAttackCode);
    let attackName = $state<string>('');
    let attackDescription = $state<string>('');
    let attackType = $state<string>('');
    let attackElement = $state<number | null>(null);
    let attackForces = $state<Array<{ element: number; value: number }>>([]);
    let attackDamage = $state<number>(0);
    let attackDiceRolls = $state<number>(0);
    let attackEffect = $state<string | null>(null);

    /*
     * Check if code is used
     * */
    const isCodeUsed = $derived.by(() => {
        return attacks?.some(attacks => attacks.code === attackCode);
    });


    // Clean second element data if firts change to the same element
    $effect (() => {
        if(attackElement) {
            let elementData = attackElement ? getElementFormatted(attackElement, data?.elements) : 'default';
            changeThemeTo(elementData ? JSON.parse(elementData)?.label : 'default');
        }
        else {
            changeThemeTo("default");
        }
    });

    /*
     * Validate form
     * */
    const isFormValid = () => {
        return (
            attackCode > 0 &&
            !isCodeUsed &&
            attackName.trim() !== '' &&
            attackElement !== null &&
            attackType.trim() !== '' &&
            attackDamage > 0
        );
    };

    /*
     * Reset form values
     * */
    const resetForm = () => {
        attackCode = nextAttackCode;
        attackName = '';
        attackDescription = '';
        attackType = '';
        attackDamage = 0;
        attackDiceRolls = 0;
        attackElement = null; // Get de id
        attackForces = [];
        attackEffect = '';

        changeThemeTo("default");
    };


    /**
     * Get element formatted data
     */
    function getElementFormatted(elementId: number | null, collection: any) {
        const item = collection.find((e: { id: number; label: string; icon: string }) => e.id === elementId) ?? null;
        return item ? JSON.stringify({ id: item.id, label: item.label, icon: item.icon }) : null;
    }

    /**
     * Get forces formatted data
    */
   function getForcesFormatted(forces: Array<{ element: number; value: number }>) {
        if (!forces || forces.length === 0) return null;

        const formatted = forces.map(force => {
            const elementData = data.elements.find(e => e.id === force.element);
            return {
                value: force.value,
                elementData: elementData
                    ? { id: elementData.id, label: elementData.label, color: elementData.color, icon: elementData.icon }
                    : null
            };
        });

        return JSON.stringify(formatted);
    }

    /**
     * Create card
     */
    const handleCreateAttack = async () => {
        if (!isFormValid()) return;

        const attackForcesString: string | null = getForcesFormatted(attackForces);

        const formData = new FormData();
        formData.append("code", String(attackCode));
        formData.append("name", attackName);
        formData.append("handle", formatHandle(attackName));
        formData.append("description", attackDescription);
        formData.append("type", attackType);
        formData.append("element", String(attackElement));
        formData.append("damage", String(attackDamage));
        formData.append("dice_rolls", String(attackDiceRolls));
        if (attackEffect) formData.append("effect", attackEffect);
        if (attackForcesString) formData.append("necessary_force", attackForcesString);


        try {
            const res = await fetch("/api/attacks", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                // si la API devuelve un error HTTP
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.message || `Error ${res.status}: ${res.statusText}`);
            }

            const newAttack = await res.json();
            console.log("Ataque creado:", newAttack.attack);

            // Actualizar array local
            attacks = [...attacks, newAttack.attack];

            resetForm();

            // puedes lanzar un toast de éxito
            alert("Ataque creado con éxito");

        } catch (err) {
            console.error("❌ Error creando el ataque:", err);
            alert(`Hubo un error al crear el ataque: ${(err as Error).message}`);
        }
    };

</script>

<div class="create-page-container">
    <div class="form-group">
        <InputNumber
            label="Código del ataque"
            bind:value={attackCode}
            error={isCodeUsed}
            minValue={1}
            maxValue={300}
            step={1}
            isMandatory={true}
            isDisabled={false}
        />
        <InputText
            type="text"
            label="Nombre"
            placeholder="Golpe cuerpo"
            bind:value={attackName}
            error={false}
            minLength={1}
            maxLength={120}
            isMandatory={true}
        />
        <InputText
            type="textarea"
            label="Descripción"
            placeholder="Es un movimiento físico de tipo Normal que causa daño y tiene una alta probabilidad de paralizar al oponente"
            bind:value={attackDescription}
            error={false}
            minLength={1}
            maxLength={300}
            isMandatory={false}
        />
        <InputText
            type="textarea"
            label="Efectos"
            placeholder="Se autolesiona, se hace -10 puntos de daño a sí mismo."
            bind:value={attackEffect}
            error={false}
            minLength={1}
            maxLength={300}
            isMandatory={false}
        />
        <Divider title="Clasificación" hasMargins={true}></Divider>
        <div class="row">
            <RadioList
                label="Tipo de ataque"
                list={[
                    {label: "Físico", value: 'physical', icon: 'physical'},
                    {label: "Mágico", value: 'magical', icon: 'magical' }
                ]}
                bind:group={attackType}
                isMandatory={true}
            />
            <Select
                label="Elemento"
                list={data.elements}
                iconType="image"
                isMandatory={true}
                isDisabled={false}
                bind:group={attackElement}
            />
        </div>
        <Divider title="Skills" hasMargins={true}></Divider>
        <div class="row">
            <InputNumber
                label="Daño"
                bind:value={attackDamage}
                error={false}
                minValue={0}
                maxValue={9000}
                step={10}
                isMandatory={true}
                isDisabled={false}
            />
            <InputNumber
                label="Tiradas de dado"
                bind:value={attackDiceRolls}
                error={false}
                minValue={0}
                maxValue={6}
                step={1}
                isMandatory={false}
                isDisabled={false}
            >
                {@html diceRollsIcon}
            </InputNumber>
        </div>
        <Divider title="Fuerza" hasMargins={true}></Divider>
        <Forces elements={data.elements} bind:forces={attackForces} />
        <div class="btn-wrapper">
            <Button
                type="primary"
                text="Crear ataque"
                onClick={handleCreateAttack}
                isDisabled={!isFormValid()}
            />
        </div>
        
    </div>
</div>


<style lang="scss">
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .create-page-container {
        width: 100%;
        padding-top: functions.rem(20);

        @include mixins.displayFlex(row, 40, center, flex-start, nowrap);
        @include mixins.margins;

        @media (max-width: 800px) {
            flex-direction: column;
            align-items: center;
        }

        .form-group {
            width: 100%;
            max-width: functions.rem(600);
            padding: functions.rem(10) 0;

            @include mixins.displayFlex(column, 28, flex-start, flex-start, wrap);

            .row {
                width: 100%;

                &:not(.min-gap){
                    @include mixins.displayFlex(row, 28, flex-start, flex-end, wrap);
                }                
            }

            .btn-wrapper {
                padding-top: functions.rem(40);
                @include mixins.displayFlex(row, 12, flex-start, flex-end, wrap);
            }
        }
    }
</style>