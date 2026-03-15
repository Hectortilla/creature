<script lang="ts">
    import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth.svelte';

    // Components
    import StylishedButton from '$lib/components/buttons/StylishedButton.svelte';


    function handleLogout() {
		authStore.clearAuth();
		goto('/login');
	}
</script>

<div class="feature-container">
    <svg class="reverse" width="100%" height="100%" viewBox="0 0 15 68" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14.0835 34C14.0835 21.2475 9.0176 9.01736 0.000242456 -1.2312e-06L0.000235558 68C9.0176 58.9826 14.0835 46.7525 14.0835 34Z" fill="currentColor"/>
    </svg>
    <ul class="feature-ul">
        {#if authStore.isAuthenticated}
            <li class="feature-li">
                <button class="logout-btn" onclick={handleLogout}>
                    {authStore.user?.username}
                </button>
            </li>
        {/if}
        <li class="feature-li">
            <a class="nav-link" href="/attacks/create">Shop</a>
        </li>
        <li class="feature-li">
            <StylishedButton
                label="Play"
                link="/game"
            />
        </li>
    </ul>
    <svg width="100%" height="100%" viewBox="0 0 15 68" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14.0835 34C14.0835 21.2475 9.0176 9.01736 0.000242456 -1.2312e-06L0.000235558 68C9.0176 58.9826 14.0835 46.7525 14.0835 34Z" fill="currentColor"/>
    </svg>
</div>

<style lang="scss">
    @use "../../styles/abstracts/variables" as variables;
	@use "../../styles/abstracts/mixins" as mixins;
	@use "../../styles/abstracts/functions" as functions;

    .feature-container {        
        height: functions.rem(68);

        @include mixins.displayFlex(row, 0, center, center, nowrap);

        svg {
            width: auto;
            color: var(--color-nav-feature-background);

            &.reverse {
                transform: rotate(180deg);
            }
        }

        .feature-ul {
            $gap-space: 20;

            height: 100%;
            background-color: var(--color-nav-feature-background);
            padding: functions.rem(8) 0 functions.rem(8) functions.rem(12);

            @include mixins.displayFlex(row, $gap-space, center, center);

            .feature-li {
                position: relative;

                &:not(:first-child) {
                    padding-left: functions.rem($gap-space);
                }

                a, button {
                    display: block;
                    position: relative;
                    font-size: functions.rem(20);
                    padding-top: functions.rem(4);
                    border: none;
                    cursor: pointer;
                    
                    @include mixins.fontProps("title", 400, 100, normal);
                    @include mixins.transition();

                    &:hover {
                        color: var(--color-nav-active-color);
                    }
                }

                &:not(:first-child)::before {
                    content: "";
                    position: absolute;
                    top: 50%;
                    left: 0;
                    transform: translateY(-50%);
                    display: block;
                    width: 1px;
                    height: functions.rem(16);
                    background-color: var(--color-nav-feature-divider);
                }
            }
        }
    }
</style>