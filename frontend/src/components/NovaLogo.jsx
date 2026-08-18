import NOVA_BRAND from "../config/brand";

export default function NovaLogo({
    className = "h-8 w-auto",
    markOnly = false,
}) {
    return (
        <img
            src={markOnly ? NOVA_BRAND.logoMark : NOVA_BRAND.logo}
            alt={NOVA_BRAND.logoAlt}
            className={className}
            draggable="false"
        />
    );
}
