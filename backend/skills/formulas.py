class FormulaSkill:

    def build(

        self,

        facts

    ):

        result=[]

        for fact in facts:

            if "=" in fact:

                result.append(fact)

        if len(result)==0:

            return None

        return "\n".join(result)