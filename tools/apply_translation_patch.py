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


def regex_once(path: str, pattern: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    matches = re.findall(pattern, text, flags=re.DOTALL)
    print(f"PATCH {path}: regex matches={len(matches)}")
    if len(matches) != 1:
        raise SystemExit(f"{path}: expected exactly 1 regex match, found {len(matches)}")
    p.write_text(re.sub(pattern, replacement, text, count=1, flags=re.DOTALL), encoding="utf-8")


LANGUAGES = [
    "English", "French", "Spanish", "German", "Italian", "Portuguese",
    "Dutch", "Polish", "Ukrainian", "Russian", "Czech", "Romanian",
    "Hungarian", "Greek", "Swedish", "Turkish", "Arabic", "Hindi",
    "Chinese", "Japanese", "Korean", "Vietnamese", "Thai", "Indonesian",
]


# Backend validation must accept the same languages already supported by
# backend/language_support.py. This changes validation only, not the schema.
replace_once(
    "backend/settings.py",
    '    ALLOWED_LANGUAGES = {\n        "English",\n        "French",\n    }',
    '    ALLOWED_LANGUAGES = {\n' + ''.join(f'        "{language}",\n' for language in LANGUAGES) + '    }'
)

# Keep the existing Settings UI structure unchanged. Only expand the values
# accepted by its existing language control.
regex_once(
    "frontend/src/pages/Settings.jsx",
    r'language:\s*\[\s*"English",\s*"French"\s*\],',
    'language: [\n' + ''.join(f'        "{language}"{"," if index < len(LANGUAGES)-1 else ""}\n' for index, language in enumerate(LANGUAGES)) + '    ],'
)

# Make the already-existing i18n layer react immediately to the selected
# setting, including when a saved preference is loaded on page entry.
replace_once(
    "frontend/src/pages/Settings.jsx",
    '    /* ========================================================\n       INITIALIZATION\n    ======================================================== */',
    '    /* ========================================================\n       LIVE INTERFACE LANGUAGE\n    ======================================================== */\n\n    useEffect(\n        () => {\n\n            try {\n\n                applyNovaLanguage(\n                    settings.language\n                );\n\n            } catch (languageError) {\n\n                console.error(\n                    "Nova interface language error:",\n                    languageError\n                );\n\n            }\n\n        },\n        [\n            settings.language\n        ]\n    );\n\n\n    /* ========================================================\n       INITIALIZATION\n    ======================================================== */'
)

for required in (
    "backend/settings.py",
    "backend/language_support.py",
    "frontend/src/pages/Settings.jsx",
    "frontend/src/i18n.js",
):
    Path(required).read_text(encoding="utf-8")

print("Translation settings patch applied successfully.")
# Guarded workflow trigger marker. No application behavior.
