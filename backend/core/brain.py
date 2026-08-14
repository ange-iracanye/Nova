from backend.pipeline.input import InputPipeline
from backend.pipeline.memory import MemoryPipeline
from backend.pipeline.knowledge import KnowledgePipeline
from backend.pipeline.reasoning import ReasoningPipeline
from backend.pipeline.response import ResponsePipeline


class Brain:

    def __init__(self):

        self.input = InputPipeline()

        self.memory = MemoryPipeline()

        self.knowledge = KnowledgePipeline()

        self.reasoning = ReasoningPipeline()

        self.response = ResponsePipeline()