<script lang="ts">
    import type { Association } from '$lib/types';
    import { formatHandle } from '$lib/utils/formatHandle';

    // Components
    import InputNumber from "$lib/components/input/Number.svelte";
    import InputText from "$lib/components/input/Text.svelte";
    import Button from "$lib/components/Button.svelte"

    interface PageProps {
        data: {
            associations?: Association[];
        };
    }
    let { data }: PageProps = $props();

    let associations = $state([...data.associations ?? []]);
    $inspect("Cards loaded:", associations);

    /*
     * Search next code in cards
     * */
    let nextAssociationCode = $derived.by(() => {
        return associations.length > 0 ? (associations[associations.length - 1]?.code + 1 || 1) : 1;
    });

    // New Card data
    let associationCode = $derived.by(() => nextAssociationCode);
    let associationName = $state<string>('');
    let associationDescription = $state<string>('');

    /*
     * Check if code is used
     * */
    const isCodeUsed = $derived.by(() => {
        return associations?.some(associations => associations.code === associationCode);
    });


    /*
     * Validate form
     * */
    const isFormValid = () => {
        return (
            associationCode > 0 &&
            !isCodeUsed &&
            associationName.trim() !== '' &&
            associationDescription.trim() !== ''
        );
    };

    /*
     * Reset form values
     * */
    const resetForm = () => {
        associationCode = nextAssociationCode;
        associationName = '';
        associationDescription = '';
    };

    /**
     * Create card
     */
    const handleCreateAssociation = async () => {
        if (!isFormValid()) return;

        const formData = new FormData();
        formData.append("code", String(associationCode));
        formData.append("name", associationName);
        formData.append("handle", formatHandle(associationName));
        formData.append("description", associationDescription);


        try {
            const res = await fetch("/api/associations", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                // si la API devuelve un error HTTP
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.message || `Error ${res.status}: ${res.statusText}`);
            }

            const newAssociation = await res.json();
            console.log("Asociación creada:", newAssociation.association);

            // Actualizar array local
            associations = [...associations, newAssociation.association];

            resetForm();

            // puedes lanzar un toast de éxito
            alert("asociación creada con éxito");

        } catch (err) {
            console.error("❌ Error creando la asociación:", err);
            alert(`Hubo un error al crear la asociación: ${(err as Error).message}`);
        }
    };

</script>

<div class="create-page-container">
    <div class="form-group">        
        <InputNumber
            label="Código de la asociación"
            bind:value={associationCode}
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
            bind:value={associationName}
            error={false}
            minLength={1}
            maxLength={120}
            isMandatory={true}
        />
        <InputText
            type="textarea"
            label="Descripción / Efecto"
            placeholder="Es un movimiento físico de tipo Normal que causa daño y tiene una alta probabilidad de paralizar al oponente"
            bind:value={associationDescription}
            error={false}
            minLength={1}
            maxLength={300}
            isMandatory={true}
        />
        <div class="btn-wrapper">
            <Button
                type="primary"
                text="Crear asociación"
                onClick={handleCreateAssociation}
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

            .btn-wrapper {
                padding-top: functions.rem(40);
                @include mixins.displayFlex(row, 12, flex-start, flex-end, wrap);
            }
        }
    }
</style>