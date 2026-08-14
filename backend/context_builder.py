class ContextBuilder:

    def build(

        self,

        retrieved,

        history

    ):

        context=[]

        for item in retrieved:

            context.append(item)

        for turn in history[-3:]:

            context.append(

                "User: "+turn["user"]

            )

            context.append(

                "Nova: "+turn["assistant"]

            )

        return "\n".join(context)