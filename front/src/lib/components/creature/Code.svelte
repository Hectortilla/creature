<script lang="ts">
    interface PageProps {
        code: number;
    }

    let { code }: PageProps = $props();
</script>

<div class="code">
    <p class:smaller={code >= 100}>{code}</p>
    <img src="/images/code-icon.png" alt="">
</div>

<style lang="scss">
    @use "../../styles/abstracts/variables" as variables;
    @use "../../styles/abstracts/mixins" as mixins;
	@use "../../styles/abstracts/functions" as functions;

    .code {
        position: relative;
        // width: functions.rem(36);
        // height: functions.rem(36);
        width: fit-content;
        height: 100%;
        aspect-ratio: 1/1;

        @include mixins.displayFlex(row, 0, center, center, nowrap);

        &::before {
            //
            //
            display: none;
            //
            content: "";
            position: absolute;
            top: 50%;
            left: 50%;
            width: 72%;
            height: 72%;
            background: linear-gradient(
                110deg,
                var(--color-creature-code-background-gradient-0) 0%,
                var(--color-creature-code-background-gradient-50) 50%,
                var(--color-creature-code-background-gradient-100) 100%,

            );
            transform: translate(-50%, -50%) rotate(45deg);
            border-radius: functions.rem(4);
            box-shadow:
                functions.rem(1) functions.rem(2) functions.rem(2) functions.rem(-2) var(--color-creature-code-light-top) inset,
                functions.rem(-1) functions.rem(-2) functions.rem(6) functions.rem(-1) var(--color-creature-code-light-bottom) inset;
        }

        p {
            position: relative;
            font-family: variables.$font-number;
            font-size: functions.rem(20);
            text-align: center;
            color: var(--color-creature-foreground);
            z-index: 2;
            text-shadow: functions.rem(-1) functions.rem(2) functions.rem(3) var(--color-creature-code-text-shadow);

            &:not(.smaller) {
                font-size: functions.rem(20);
            }
            &.smaller {
                font-size: functions.rem(19);
                letter-spacing: functions.rem(-1);
            }
        }

        img {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
        }

    }
</style>