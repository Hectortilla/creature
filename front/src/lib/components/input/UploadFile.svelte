<script lang="ts">
    import { formatHandle } from '$lib/utils/formatHandle';

    // Components
    import Button from '$lib/components/Button.svelte';

    interface Props {
        buttonText: string;
        handleFileChange: (event: Event) => void;
    }
    let { buttonText, handleFileChange }: Props = $props();

    let fileInput = $state<HTMLInputElement | null>(null);
    let fileName = $state<string | null>(null);

    function triggerFileDialog() {
        fileInput?.click();
    }

    function onFileChange(event: Event) {
        handleFileChange(event);

        const target = event.target as HTMLInputElement;
        const file = target.files?.[0] ?? null;
        fileName = file ? file.name : null;
    }
</script>

<div class="input-wrapper">
    <input
        id={formatHandle(buttonText)}
        type="file"
        accept="image/*"
        bind:this={fileInput}
        onchange={(event) => {onFileChange(event)}}
        style="display:none"
    />

    <Button
        type="secondary"
        text={buttonText}
        isDisabled={false}
        onClick={() => {triggerFileDialog()}}
    />
    <p>{fileName ? fileName : 'Ningún archivo seleccionado'}</p>

</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .input-wrapper {
        background-color: var(--color-pop-in-background);
        border-radius: functions.rem(variables.$input-radius);
        padding-right: functions.rem(20);

        @include mixins.displayFlex(row, 10, flex-start, center, wrap);

        p {
            color: var(--color-input-placeholder);
            font-size: functions.rem(14);
        }
    }
</style>
