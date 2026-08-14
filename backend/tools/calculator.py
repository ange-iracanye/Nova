import re


class Calculator:

    def solve(

        self,

        text

    ):

        if re.fullmatch(

            r"[0-9+\-*/(). ]+",

            text.strip()

        ):

            try:

                return str(

                    eval(

                        text,

                        {},

                        {}

                    )

                )

            except:

                return None

        return None