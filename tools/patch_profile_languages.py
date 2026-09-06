from pathlib import Path

languages = [
    "English", "French", "Spanish", "German", "Italian", "Portuguese",
    "Dutch", "Polish", "Ukrainian", "Russian", "Czech", "Romanian",
    "Hungarian", "Greek", "Swedish", "Turkish", "Arabic", "Hindi",
    "Chinese", "Japanese", "Korean", "Vietnamese", "Thai", "Indonesian",
]

path = Path("frontend/src/pages/Settings.jsx")
text = path.read_text(encoding="utf-8")
old = '''                                    options={[
                                        [
                                            "English",
                                            "English"
                                        ],
                                        [
                                            "French",
                                            "French"
                                        ]
                                    ]}'''
new = '''                                    options={[
''' + ''.join(f'''                                        [
                                            "{language}",
                                            "{language}"
                                        ]{"," if index < len(languages) - 1 else ""}
''' for index, language in enumerate(languages)) + '''                                    ]}'''
count = text.count(old)
print(f"Profile language selector exact matches={count}")
if count != 1:
    raise SystemExit("Expected exactly one existing Profile language selector block")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Profile language selector patched successfully.")
# Guarded workflow trigger marker. No application behavior.
