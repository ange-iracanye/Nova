class MemoryPipeline:

    def process(self, message, conversation):

        last = conversation.last()

        return {

            "message": message,

            "last": last

        }