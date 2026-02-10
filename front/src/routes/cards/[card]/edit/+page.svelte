<script lang="ts">
    import type { Creature, Element, Type, Character, Attack, Ability, Association } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';
    import { changeThemeTo } from '$lib/utils/changeThemeTo';
    import { onMount, onDestroy } from 'svelte';

    // Components
    import CreatureCard360 from "$lib/components/creature/Card360.svelte"
    import InputNumber from "$lib/components/input/Number.svelte";
    import InputText from "$lib/components/input/Text.svelte";
    import SelectCard from "$lib/components/input/SelectCard.svelte"
    import SelectAttack from "$lib/components/input/SelectAttack.svelte"
    import SelectAbility from "$lib/components/input/SelectAbility.svelte"
    import SelectAssociation from "$lib/components/input/SelectAssociation.svelte"
    import RadioList from "$lib/components/input/RadioList.svelte"
    import Divider from "$lib/components/Divider.svelte"
    import UploadFile from "$lib/components/input/UploadFile.svelte"
    import Select from "$lib/components/input/Select.svelte"
    import Forces from "$lib/components/input/Forces.svelte"
    import Button from "$lib/components/Button.svelte"

    // Icons
    import healthIcon from "$lib/assets/icons/health.svg?raw"
    import physicalDefenceIcon from "$lib/assets/icons/physical-type.svg?raw"
    import magicDefenceIcon from "$lib/assets/icons/magical-type.svg?raw"

    interface PageProps {
        data: {
            cards?: Creature[];
            all_cards?: Creature[];
            elements: Element[];
            types: Type[];
            characters: Character[];
            attacks: Attack[];
            abilities: Ability[];
            associations: Association[];
        };
    }
    let { data }: PageProps = $props();
    console.log(data);

    let cards = $state([...data.all_cards ?? []]);
    let card = $state(data.cards && data.cards.length === 1 ? data.cards[0] : null);

    /*
     * Search next code in cards
     * */
    let nextCardCode = $derived.by(() => {
        return cards.length > 0 ? (cards[cards.length - 1]?.code + 1 || 1) : 1;
    });

    // Inicialización de estados en edit
    let cardCode = $state(card?.code ?? 1);
    let cardName = $state(card?.name ?? '');
    let cardIsEvolution = $state(card?.is_evolution ? true : false);
    let evolutionNumber = $state(card?.is_evolution?.code ?? 1);
    let cardDescription = $state(card?.description ?? '');
    let cardImage: File | null = null;
    let cardOverlayImage: File | null = null;
    let cardFirstElement = $state(card?.first_element?.id ?? null);
    let cardSecondElement = $state(card?.second_element?.id ?? null);
    let cardType = $state(card?.type?.id ?? null);
    let cardCharacter = $state(card?.character?.id ?? null);
    let cardFirstAttack = $state(card?.first_attack?.code ?? null);
    let cardSecondAttack = $state(card?.second_attack?.code ?? null);
    let cardHealth = $state(card?.health ?? 0);
    let cardPhysicalDefence = $state(card?.physical_defence ?? 0);
    let cardMagicDefence = $state(card?.magic_defence ?? 0);
    let cardForces = $state(
        card?.forces && Array.isArray(card.forces) 
            ? (card.forces as Array<{ elementData: { id: number }; value: number }>).map(f => ({ element: f.elementData.id, value: f.value })) 
            : []
    );
    let cardAbility = $state(card?.ability?.code ?? null);
    let cardAssociation = $state(card?.association?.code ?? null);


    // Preview
    let cardImagePreview = $state(card?.image ?? null);
    let cardOverlayImagePreview = $state(card?.overlay_image ?? null);

    /*
     * Check if code is used
     * */
        let isCodeUsed = $state(false);

    $effect(() => {
        isCodeUsed = cards?.some(c => c.code === cardCode && c.id !== card?.id) ?? false;
    });


    /**
     * Second element list without first element
     */
    let secondElementsList = $derived.by(() => {
        return data.elements.filter(e => e.id !== cardFirstElement); 
    });

    // Clean second element data if firts change to the same element
    $effect (() => {
        if(cardFirstElement === cardSecondElement) {
            cardSecondElement = null;
        }

        if(cardFirstElement && cardFirstElement !== null) {
            let elementData = cardFirstElement ? getElementFormatted(cardFirstElement, data?.elements) : 'default';
            changeThemeTo(elementData ? JSON.parse(elementData)?.label : 'default');
        }
        else {
            changeThemeTo("default");
        }
    });

    /**
     * Second attack list without first attack
     */
    let secondAttackList = $derived.by(() => {
        return data.attacks.filter(e => e.code !== cardFirstAttack); 
    });

    // Clean second attack data if firts change to the same element
    $effect (() => {
        if(cardFirstAttack === cardSecondAttack) {
            cardSecondAttack = null;
        }
        if (cardFirstAttack === null && cardSecondAttack !== null) {
            cardFirstAttack = cardSecondAttack;
            cardSecondAttack = null;
        }
    });

    /*
     * Validate form
     * */
    const isFormValid = () => {
        return (
            cardCode > 0 &&
            !isCodeUsed &&
            cardName.trim() !== '' &&
            //cardDescription.trim() !== '' &&
            cardFirstElement !== null &&
            cardType !== null &&
            cardCharacter !== null &&
            cardHealth >= 0 &&
            cardPhysicalDefence >= 0 &&
            cardMagicDefence >= 0 &&
            cardFirstAttack !== null
        );
    };


    /**
     * Handle upload image
    */
    function handleImageChange(e: Event) {
        const files = (e.target as HTMLInputElement).files;
        cardImage = files && files.length > 0 ? files[0] : null;

        if (cardImage) {
            // crea una URL temporal para previsualización
            cardImagePreview = URL.createObjectURL(cardImage);
        } else {
            cardImagePreview = null;
        }
    }

    function handleOverlayImageChange(e: Event) {
        const files = (e.target as HTMLInputElement).files;
        cardOverlayImage = files && files.length > 0 ? files[0] : null;

        if (cardOverlayImage) {
            // crea una URL temporal para previsualización
            cardOverlayImagePreview = URL.createObjectURL(cardOverlayImage);
        } else {
            cardOverlayImagePreview = null;
        }
    }

    // libera memoria al desmontar el componente
    onDestroy(() => {
        if (cardImagePreview) URL.revokeObjectURL(cardImagePreview);
        if (cardOverlayImagePreview) URL.revokeObjectURL(cardOverlayImagePreview);
        changeThemeTo("default");
    });

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
    const handleUpdateCard = async () => {
        if (!isFormValid() || !card) return;

        const cardForcesString: string | null = getForcesFormatted(cardForces);

        const formData = new FormData();
        formData.append("id", String(card.id));
        formData.append("code", String(cardCode));
        formData.append("name", cardName);
        formData.append("is_evolution", String(cardIsEvolution ? evolutionNumber : null));
        formData.append("description", cardDescription);
        formData.append("first_element", String(cardFirstElement));
        formData.append("second_element", String(cardSecondElement));
        formData.append("type", String(cardType));
        formData.append("character", String(cardCharacter));
        formData.append("first_attack", String(cardFirstAttack));
        formData.append("second_attack", String(cardSecondAttack));
        formData.append("health", String(cardHealth));
        formData.append("physical_defence", String(cardPhysicalDefence));
        formData.append("magic_defence", String(cardMagicDefence));
        formData.append("ability", String(cardAbility));
        formData.append("association", String(cardAssociation));
        if (cardImage) formData.append("image", cardImage);
        if (cardOverlayImage) formData.append("overlay_image", cardOverlayImage);
        if (cardForcesString) formData.append("forces", cardForcesString);

        try {
            const res = await fetch(`/api/cards/${card.code}`, {
                method: "PUT",
                body: formData
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.message || `Error ${res.status}: ${res.statusText}`);
            }

            const updatedCard = await res.json();
            console.log("Carta actualizada:", updatedCard.card);

            alert("Carta actualizada con éxito");
        } catch (err) {
            console.error("❌ Error actualizando la carta:", err);
            alert(`Hubo un error al actualizar la carta: ${(err as Error).message}`);
        }
    };

    /// Creature card preview
    let cardContainer = $state<HTMLElement>();
    let cardContainerPosition = $state(0);

    // Get Data Preview
    const firstElement = $derived.by(() => data.elements?.find(e => e.id === cardFirstElement));
    const secondElement = $derived.by(() => data.elements?.find(e => e.id === cardSecondElement));
    const type = $derived.by(() => data.types?.find(e => e.id === cardType));
    const character = $derived.by(() => data.characters?.find(e => e.id === cardCharacter));

    let dataCardPreview = $derived.by(() => {
        return {
            id: card?.id ?? 0,
            created_at: card?.created_at ?? new Date().toISOString(),
            code: cardCode,
            name: cardName,
            is_evolution: cardIsEvolution ? { id: 0, created_at: '', code: evolutionNumber, name: '', handle: '', description: null, image: null, overlay_image: null, health: null, physical_defence: null, magic_defence: null, forces: null, is_evolution_id: null, first_element_id: null, second_element_id: null, type_id: null, character_id: null, first_attack_id: null, second_attack_id: null, ability_id: null, association_id: null } : null,
            handle: formatHandle(cardName),
            image: cardImagePreview,
            overlay_image: cardOverlayImagePreview,
            first_element: firstElement,
            second_element: secondElement,
            type: type,
            character: character,
        } as import('$lib/types').Creature;
    });

    onMount (() => {
        cardContainerPosition = cardContainer?.getBoundingClientRect().top ?? 0;
    });

    $effect(() => {
        //$inspect(cardForces);
        //$inspect(getForcesFormatted(cardForces));
    });
</script>

<div class="create-page-container">
    <div class="card-wrapper" bind:this={cardContainer}>
        <CreatureCard360
            data={dataCardPreview}
            key={1}
            showCode={true}
            showInfo={true}
            allowLink= {false}
            allowHoverEffect={true}
            containerPos={cardContainerPosition}
        />
    </div>
    <div class="form-group">
        <InputNumber
            label="Código de la carta"
            bind:value={cardCode}
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
            placeholder="Dragón blanco de ojos azules"
            bind:value={cardName}
            error={false}
            minLength={1}
            maxLength={120}
            isMandatory={true}
        />
        <InputText
            type="textarea"
            label="Descripción"
            placeholder="Lagarto bípedo, caracterizado por la llama en la punta de su cola, que indica su estado de ánimo y salud..."
            bind:value={cardDescription}
            error={false}
            minLength={1}
            maxLength={300}
            isMandatory={false}
        />
        <UploadFile
            buttonText="Seleccionar imagen de carta"
            handleFileChange={(event) => handleImageChange(event)}
        />
        <UploadFile
            buttonText="Seleccionar imagen overlay"
            handleFileChange={(event) => handleOverlayImageChange(event)}
        />
        <Divider title="Evolución" hasMargins={true}></Divider>
        <RadioList
            label="¿Es una evolución?"
            list={[
                {label: "Si", value: true},
                {label: "No", value: false}
            ]}
            bind:group={cardIsEvolution}
            isMandatory={true}
        />
        <div class="row min-gap">
            <InputNumber
                label="Carta pre-evolución"
                bind:value={evolutionNumber}
                error={false}
                minValue={1}
                maxValue={cards.length}
                step={1}
                isMandatory={false}
                isDisabled={!cardIsEvolution}
            />
            <SelectCard
                cards={cards}
                bind:group={evolutionNumber}
                buttonText="Buscar carta"
                isDisabled={!cardIsEvolution}
            />
            <p class="selected-card" class:disabled={!cardIsEvolution}>
                {`Carta seleccionada: ${cards && cardIsEvolution ? cards?.find(card => card.code === evolutionNumber)?.name ?? "Invalido" : "No seleccionado"}`}
            </p>
        </div>
        <Divider title="Clasificación" hasMargins={true}></Divider>
        <div class="row">
            <Select
                label="Tipo"
                list={data.types}
                iconType="icon"
                isMandatory={true}
                isDisabled={false}
                bind:group={cardType}
            />
            <Select
                label="Naturaleza"
                list={data.characters}
                iconType="icon"
                isMandatory={true}
                isDisabled={false}
                bind:group={cardCharacter}
            />
            <Select
                label="Primer elemento"
                list={data.elements}
                iconType="image"
                isMandatory={true}
                isDisabled={false}
                bind:group={cardFirstElement}
            />
            <Select
                label="Segundo elemento"
                list={secondElementsList}
                iconType="image"
                isMandatory={false}
                isDisabled={!cardFirstElement}
                bind:group={cardSecondElement}
            />
        </div>
        <Divider title="Skills" hasMargins={true}></Divider>
        <div class="row">
            <InputNumber
                label="Vida"
                bind:value={cardHealth}
                error={false}
                minValue={0}
                maxValue={9000}
                step={10}
                isMandatory={true}
                isDisabled={false}
                showInfo={true}
            >
                {@html healthIcon}
            </InputNumber>
            <InputNumber
                label="Defensa física"
                bind:value={cardPhysicalDefence}
                error={false}
                minValue={0}
                maxValue={300}
                step={10}
                isMandatory={true}
                isDisabled={false}
                showInfo={true}
            >
                {@html physicalDefenceIcon}
            </InputNumber>
            <InputNumber
                label="Defensa mágica"
                bind:value={cardMagicDefence}
                error={false}
                minValue={0}
                maxValue={300}
                step={10}
                isMandatory={true}
                isDisabled={false}
                showInfo={true}
            >
                {@html magicDefenceIcon}
            </InputNumber>
        </div>
        <Divider title="Fuerza" hasMargins={true}></Divider>
        <Forces elements={data.elements} bind:forces={cardForces} />
        <Divider title="Ataques" hasMargins={true}></Divider>
        <div class="row min-gap">
            <SelectAttack
                attacks={data.attacks}
                bind:group={cardFirstAttack}
                buttonText="Añadir ataque *"
                isDisabled={false}
            />
            <SelectAttack
                attacks={secondAttackList}
                bind:group={cardSecondAttack}
                buttonText="Añadir ataque"
                isDisabled={cardFirstAttack === null}
            />
        </div>
        <Divider title="Efectos" hasMargins={true}></Divider>
            <SelectAbility
                abilities={data.abilities}
                bind:group={cardAbility}
                buttonText="Añadir Habilidad"
                isDisabled={false}
            />
        <Divider title="Asociaciones" hasMargins={true}></Divider>
            <SelectAssociation
                associations={data.associations}
                bind:group={cardAssociation}
                buttonText="Añadir Asociación"
                isDisabled={false}
            />
        <div class="btn-wrapper">
            <Button
                type="primary"
                text="Guardar carta"
                onClick={handleUpdateCard}
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
        padding-top: functions.rem(60);

        @include mixins.displayFlex(row, 40, center, flex-start, nowrap);
        @include mixins.margins;

        @media (max-width: 800px) {
            flex-direction: column;
            align-items: center;
        }

        .card-wrapper {
            position: sticky;
            top: functions.rem(40);
            left: 0;
            width: 90dvw;
            max-width: functions.rem(300);
            perspective: 1000px;
            z-index: 2;

            @media (max-width: 800px) {
                position: relative;
                top: inherit;
                left: inherit;
                width: 70dvw;
            }
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

                &.min-gap{
                    @include mixins.displayFlex(row, 10, flex-start, flex-end, wrap);
                }

                .selected-card {
                    width: 100%;
                    color: var(--color-input-placeholder);
                    font-size: functions.rem(14);
                    padding: 0 functions.rem(8);
                }
                
            }

            .btn-wrapper {
                padding-top: functions.rem(40);
                @include mixins.displayFlex(row, 12, flex-start, flex-end, wrap);
            }
        }
    }
</style>