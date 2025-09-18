import { formatHandle } from "./formatHandle";

function clearThemeClasses() {
    if (typeof document === "undefined") return;

    document.body.classList.forEach(cls => {
        if (cls.startsWith("theme-")) {
            document.body.classList.remove(cls);
        }
    });
}

export function changeThemeTo(theme: string | undefined) {
    if (typeof document === "undefined") return;

    // Siempre limpia antes
    clearThemeClasses();

    if (!theme) {
        document.body.classList.add("theme-default");
    } else {
        document.body.classList.add(`theme-${formatHandle(theme)}`);
    }
}
