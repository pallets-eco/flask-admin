// Custom js to apply active class to all theme option links
document.addEventListener("DOMContentLoaded", () => {
    const html = document.documentElement;
    const body = document.body;

    const currentValues = {
        layout: body.getAttribute("data-tabler-layout"),
        theme_primary: html.getAttribute("data-bs-theme-primary"),
        theme_base: html.getAttribute("data-bs-theme-base"),
        theme_font: html.getAttribute("data-bs-theme-font"),
        theme_radius: html.getAttribute("data-bs-theme-radius")
    };

    Object.keys(currentValues).forEach(field => {
        document.querySelectorAll(`.user-${field}-options`).forEach(el => {
            const url = new URL(el.href, window.location.origin);
            const value = url.searchParams.get("value");
            el.classList.toggle("active", value === currentValues[field]);
        });
    });
});
