class ResponsePipeline:

    def process(self, builder, message, facts):

        return builder.build(message, facts)