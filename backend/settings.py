import json
from pathlib import Path


class SettingsManager:

    def __init__(self):

        self.file = Path(
            "data/settings.json"
        )

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if self.file.exists():

            try:

                self.data = json.loads(
                    self.file.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception:

                self.data = self.default_settings()

                self.save()

        else:

            self.data = self.default_settings()

            self.save()

        self.ensure_defaults()


    # =====================================
    # DEFAULT SETTINGS
    # =====================================

    def default_settings(self):

        return {

            # ==============================
            # PROFILE
            # ==============================

            "name": "",

            "language": "English",

            "level": "High School",


            # ==============================
            # TEACHING
            # ==============================

            "teaching_style": "adaptive",

            "difficulty": "adaptive",

            "hints": "when_needed",

            "step_by_step": True,

            "adaptive_learning": True,


            # ==============================
            # RESPONSE
            # ==============================

            "response_length": "balanced",

            "tone": "friendly",

            "use_examples": True,

            "use_analogies": True,

            "encouragement": True,


            # ==============================
            # CORRECTIONS
            # ==============================

            "correction_style": "explain",

            "show_correct_answer": True,


            # ==============================
            # AI
            # ==============================

            "creativity": "medium",


            # ==============================
            # PERSONALIZATION
            # ==============================

            "behavior": "",

            "custom_instructions": ""
        }


    # =====================================
    # ENSURE DEFAULTS
    # =====================================

    def ensure_defaults(self):

        defaults = self.default_settings()

        changed = False

        for key, value in defaults.items():

            if key not in self.data:

                self.data[key] = value

                changed = True

        if changed:

            self.save()


    # =====================================
    # SAVE
    # =====================================

    def save(self):

        self.file.write_text(

            json.dumps(
                self.data,
                indent=4,
                ensure_ascii=False
            ),

            encoding="utf-8"
        )


    # =====================================
    # GET
    # =====================================

    def get(self):

        return dict(self.data)


    # =====================================
    # UPDATE
    # =====================================

    def update(
        self,
        name=None,
        language=None,
        level=None,
        teaching_style=None,
        difficulty=None,
        hints=None,
        step_by_step=None,
        adaptive_learning=None,
        response_length=None,
        tone=None,
        use_examples=None,
        use_analogies=None,
        encouragement=None,
        correction_style=None,
        show_correct_answer=None,
        creativity=None,
        behavior=None,
        custom_instructions=None
    ):

        values = {

            "name": name,
            "language": language,
            "level": level,

            "teaching_style":
                teaching_style,

            "difficulty":
                difficulty,

            "hints":
                hints,

            "step_by_step":
                step_by_step,

            "adaptive_learning":
                adaptive_learning,

            "response_length":
                response_length,

            "tone":
                tone,

            "use_examples":
                use_examples,

            "use_analogies":
                use_analogies,

            "encouragement":
                encouragement,

            "correction_style":
                correction_style,

            "show_correct_answer":
                show_correct_answer,

            "creativity":
                creativity,

            "behavior":
                behavior,

            "custom_instructions":
                custom_instructions
        }


        for key, value in values.items():

            if value is not None:

                self.data[key] = value


        self.save()

        return self.get()