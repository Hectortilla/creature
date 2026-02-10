type ParallaxOptions = {
    intensity?: number;
    reverse?: boolean;
    speed?: number;
};

export function parallax(node: HTMLElement, options: ParallaxOptions = {}) {
    let { intensity = 15, reverse = true, speed = 50 } = options;

    let currentX = 0;
    let currentY = 0;
    let targetX = 0;
    let targetY = 0;

    function animate() {
        currentX += (targetX - currentX) * (speed / 1000);
        currentY += (targetY - currentY) * (speed / 1000);
        node.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
        requestAnimationFrame(animate);
    }

    function handleMouseMove(e: MouseEvent) {
        const { innerWidth, innerHeight } = window;
        const x = (e.clientX / innerWidth - 0.5) * 2;
        const y = (e.clientY / innerHeight - 0.5) * 2;

        const factor = reverse ? -1 : 1;

        targetX = x * intensity * factor;
        targetY = y * intensity * factor;
    }

    animate();

    window.addEventListener("mousemove", handleMouseMove);

    return {
        update(newOptions: ParallaxOptions) {
            intensity = newOptions.intensity ?? intensity;
            reverse = newOptions.reverse ?? reverse;
            speed = newOptions.speed ?? speed;
        },
        destroy() {
            window.removeEventListener("mousemove", handleMouseMove);
        }
    };
}
