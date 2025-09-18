<script lang="ts">
    import type { Ability } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';

    // Components
    import InputNumber from "$lib/components/input/Number.svelte";
    import InputText from "$lib/components/input/Text.svelte";
    import RadioList from "$lib/components/input/RadioList.svelte"
    import Divider from "$lib/components/Divider.svelte"
    import Button from "$lib/components/Button.svelte"

    interface PageProps {
        data: {
            abilities?: Ability[];
        };
    }
    let { data }: PageProps = $props();

    let abilities = $state([...data.abilities ?? []]);
    $inspect("Cards loaded:", abilities);

    /*
     * Search next code in cards
     * */
    let nextAbilityCode = $derived.by(() => {
        return abilities.length > 0 ? (abilities[abilities.length - 1]?.code + 1 || 1) : 1;
    });

    // New Card data
    let abilityCode = $derived.by(() => nextAbilityCode);
    let abilityName = $state<string>('');
    let abilityDescription = $state<string>('');
    let abilityType = $state<string>('');

    /*
     * Check if code is used
     * */
    const isCodeUsed = $derived.by(() => {
        return abilities?.some(ability => ability.code === abilityCode);
    });


    /*
     * Validate form
     * */
    const isFormValid = () => {
        return (
            abilityCode > 0 &&
            !isCodeUsed &&
            abilityName.trim() !== '' &&
            abilityDescription.trim() !== '' &&
            abilityType.trim() !== ''
        );
    };

    /*
     * Reset form values
     * */
    const resetForm = () => {
        abilityCode = nextAbilityCode;
        abilityName = '';
        abilityDescription = '';
        abilityType = '';
    };

    /**
     * Create card
     */
    const handleCreateAbility = async () => {
        if (!isFormValid()) return;

        const formData = new FormData();
        formData.append("code", String(abilityCode));
        formData.append("name", abilityName);
        formData.append("handle", formatHandle(abilityName));
        formData.append("description", abilityDescription);
        formData.append("type", abilityType);


        try {
            const res = await fetch("/api/abilities", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                // si la API devuelve un error HTTP
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.message || `Error ${res.status}: ${res.statusText}`);
            }

            const newAbility = await res.json();
            console.log("Habilidad creada:", newAbility.ability);

            // Actualizar array local
            abilities = [...abilities, newAbility.ability];

            resetForm();

            // puedes lanzar un toast de éxito
            alert("Habilidad creada con éxito");

        } catch (err) {
            console.error("❌ Error creando la habilidad:", err);
            alert(`Hubo un error al crear la habilidad: ${(err as Error).message}`);
        }
    };

</script>

<div class="create-page-container">
    <div class="form-group">        
        <InputNumber
            label="Código de la habilidad"
            bind:value={abilityCode}
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
            bind:value={abilityName}
            error={false}
            minLength={1}
            maxLength={120}
            isMandatory={true}
        />
        <InputText
            type="textarea"
            label="Descripción / Efecto"
            placeholder="Es un movimiento físico de tipo Normal que causa daño y tiene una alta probabilidad de paralizar al oponente"
            bind:value={abilityDescription}
            error={false}
            minLength={1}
            maxLength={300}
            isMandatory={true}
        />
        <Divider title="Clasificación" hasMargins={true}></Divider>
        <div class="row">
            <RadioList
                label="Tipo de habilidad"
                list={[
                    {label: "Físico", value: 'physical', icon: 'physical'},
                    {label: "Mágico", value: 'magical', icon: 'magical' }
                ]}
                bind:group={abilityType}
                isMandatory={true}
            />
        </div>
        <div class="btn-wrapper">
            <Button
                type="primary"
                text="Crear habilidad"
                onClick={handleCreateAbility}
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