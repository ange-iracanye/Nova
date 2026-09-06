from pathlib import Path
import re


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    print(f"PATCH {path}: exact matches={count}")
    if count != 1:
        raise SystemExit(f"{path}: expected exactly 1 match, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# API: scope settings endpoints to the authenticated/requested user.
replace_once("backend/api.py", "from backend.settings import SettingsManager\n", "from backend.settings import SettingsManager\nfrom backend.user_settings import set_current_user, reset_current_user\n")
replace_once("backend/api.py", 'class SettingsRequest(BaseModel):\n\n    model_config = ConfigDict(\n        extra="ignore"\n    )\n\n    name: str = ""\n', 'class SettingsRequest(BaseModel):\n\n    model_config = ConfigDict(\n        extra="ignore"\n    )\n\n    # Compatibility field for clients that identify the account by email.\n    email: Optional[str] = None\n\n    name: str = ""\n')
replace_once("backend/api.py", "def get_settings():\n\n    try:\n\n        result = settings_manager.get()\n", "def get_settings(\n    http_request: Request,\n    email: Optional[str] = Query(default=None)\n):\n\n    user_email = resolve_user_email(\n        http_request,\n        email\n    )\n\n    settings_token = set_current_user(user_email)\n\n    try:\n\n        result = settings_manager.get()\n")
replace_once("backend/api.py", '        raise HTTPException(\n\n            status_code=500,\n\n            detail="Could not load settings."\n        )\n\n    if not isinstance(\n', '        raise HTTPException(\n\n            status_code=500,\n\n            detail="Could not load settings."\n        )\n\n    finally:\n\n        reset_current_user(settings_token)\n\n    if not isinstance(\n')
replace_once("backend/api.py", "def update_settings(\n    request: SettingsRequest\n):\n\n    try:\n\n        result = settings_manager.update(\n", "def update_settings(\n    request: SettingsRequest,\n    http_request: Request\n):\n\n    user_email = resolve_user_email(\n        http_request,\n        request.email\n    )\n\n    settings_token = set_current_user(user_email)\n\n    try:\n\n        result = settings_manager.update(\n")
replace_once("backend/api.py", '        raise HTTPException(\n\n            status_code=500,\n\n            detail="Could not update settings."\n        )\n\n    return {\n\n        "success":\n            True,\n\n        "settings":\n', '        raise HTTPException(\n\n            status_code=500,\n\n            detail="Could not update settings."\n        )\n\n    finally:\n\n        reset_current_user(settings_token)\n\n    return {\n\n        "success":\n            True,\n\n        "settings":\n')
replace_once("backend/api.py", "def reset_settings():\n\n    reset_function = getattr(\n", "def reset_settings(\n    http_request: Request,\n    email: Optional[str] = Query(default=None)\n):\n\n    user_email = resolve_user_email(\n        http_request,\n        email\n    )\n\n    settings_token = set_current_user(user_email)\n\n    reset_function = getattr(\n")
replace_once("backend/api.py", '    if not callable(\n        reset_function\n    ):\n\n        return error_response(\n', '    if not callable(\n        reset_function\n    ):\n\n        reset_current_user(settings_token)\n\n        return error_response(\n')
replace_once("backend/api.py", '        raise HTTPException(\n\n            status_code=500,\n\n            detail="Could not reset settings."\n        )\n\n    return {\n', '        raise HTTPException(\n\n            status_code=500,\n\n            detail="Could not reset settings."\n        )\n\n    reset_current_user(settings_token)\n\n    return {\n')

# NovaCore: scope the already-existing settings stage to the current user.
replace_once("backend/core/nova_core.py", "from backend.settings import SettingsManager\n", "from backend.settings import SettingsManager\nfrom backend.user_settings import set_current_user, reset_current_user\n")
replace_once("backend/core/nova_core.py", "        request = None\n\n        self.last_error = None\n", "        request = None\n\n        settings_token = None\n\n        self.last_error = None\n")
replace_once("backend/core/nova_core.py", "            self.current_request = request\n\n            self.last_request_id = (\n", "            self.current_request = request\n\n            settings_token = set_current_user(request.user_email)\n\n            self.last_request_id = (\n")
replace_once("backend/core/nova_core.py", "            if request is not None:\n\n                self.last_request_duration_ms = (\n                    request.duration_ms()\n                )\n", "            if settings_token is not None:\n\n                reset_current_user(settings_token)\n\n            if request is not None:\n\n                self.last_request_duration_ms = (\n                    request.duration_ms()\n                )\n")

# Install the compatibility scoping hook before long-lived managers are used.
replace_once("backend/__init__.py", "try:\n    from backend.settings import SettingsManager as _NovaSettingsManager\n", "try:\n    import backend.user_settings  # noqa: F401\n    from backend.settings import SettingsManager as _NovaSettingsManager\n")

# Frontend. Regex is deliberately whitespace-tolerant because formatting is not behavior.
def regex_once(path: str, pattern: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    matches = re.findall(pattern, text, flags=re.DOTALL)
    print(f"PATCH {path}: regex matches={len(matches)}")
    if len(matches) != 1:
        raise SystemExit(f"{path}: expected exactly 1 regex match, found {len(matches)}")
    p.write_text(re.sub(pattern, replacement, text, count=1, flags=re.DOTALL), encoding="utf-8")

regex_once("frontend/src/pages/Settings.jsx", r'const API_URL\s*=\s*"http://127\.0\.0\.1:8000";', 'const API_URL =\n    "";')
regex_once("frontend/src/pages/Settings.jsx", r'const response\s*=\s*await fetchWithTimeout\(\s*SETTINGS_ENDPOINT\s*\);', 'const settingsUrl =\n                        user?.email\n                            ? `${SETTINGS_ENDPOINT}?email=${encodeURIComponent(user.email)}`\n                            : SETTINGS_ENDPOINT;\n\n                    const response =\n                        await fetchWithTimeout(\n                            settingsUrl,\n                            {\n                                credentials: "include"\n                            }\n                        );')

# Both API reads are wrapped in { success, settings }. Normalize each one.
regex_once("frontend/src/pages/Settings.jsx", r'sanitizeSettings\(\s*data\s*\)', 'sanitizeSettings(\n                            data?.settings ||\n                            data\n                        )')
regex_once("frontend/src/pages/Settings.jsx", r'const payload\s*=\s*sanitizeSettings\(\s*settings\s*\);\s*\n\s*try\s*\{', 'const payload =\n            sanitizeSettings(\n                settings\n            );\n\n        const requestPayload = {\n            ...payload,\n            ...(user?.email ? { email: user.email } : {})\n        };\n\n        try {')
regex_once("frontend/src/pages/Settings.jsx", r'body:\s*JSON\.stringify\(\s*payload\s*\)', 'body:\n                            JSON.stringify(\n                                requestPayload\n                            ),\n\n                        credentials:\n                            "include"')
regex_once("frontend/src/pages/Settings.jsx", r'const normalized\s*=\s*sanitizeSettings\(\s*data\s*\);', 'const normalized =\n                sanitizeSettings(\n                    data?.settings ||\n                    data\n                );')

for required in (
    "backend/api.py",
    "backend/core/nova_core.py",
    "backend/__init__.py",
    "backend/user_settings.py",
    "frontend/src/pages/Settings.jsx",
):
    Path(required).read_text(encoding="utf-8")

print("Guarded user-settings patch applied successfully.")
