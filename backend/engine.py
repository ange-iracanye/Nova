from retrieval.search import KnowledgeSearch
from knowledge.loader import KnowledgeLoader
from backend.conversation_manager import ConversationManager
from backend.profile_manager import ProfileManager
from backend.response_builder import ResponseBuilder
from backend.answer_formatter import AnswerFormatter
from backend.knowledge.answer_generator import AnswerGenerator
from backend.tools.calculator import Calculator
from backend.internet.internet_manager import InternetManager
from backend.skill_manager import SkillManager
from backend.intent_detector import IntentDetector
from backend.llm import LocalLLM
from backend.memory import Memory


class NovaEngine:
    """Compatibility engine for the original non-API Nova interface.

    V1 uses NovaCore, but this path remains useful for local scripts and
    examples. It now calls LocalLLM using the current system/user interface.
    """

    def __init__(self):
        loader = KnowledgeLoader()
        self.search = loader.load()
        self.conversation = ConversationManager()
        self.profile = ProfileManager()
        self.builder = ResponseBuilder()
        self.formatter = AnswerFormatter()
        self.generator = AnswerGenerator()
        self.calc = Calculator()
        self.internet = InternetManager()
        self.intent = IntentDetector()
        self.skills = SkillManager()
        self.llm = LocalLLM()
        self.memory = Memory()

    def _llm_answer(self, message, context):
        return self.llm.answer(
            system="You are Nova, a helpful educational assistant. Use the supplied knowledge as evidence and explain clearly.",
            user=f"Knowledge:\n{context}\n\nQuestion:\n{message}",
        )

    def reply(self, message):
        message = message.strip()
        self.profile.add_question()
        intent = self.intent.detect(message)

        answer = self.calc.solve(message)
        if answer:
            self.conversation.add(message, answer)
            self.memory.remember("User: " + message + "\nNova: " + answer)
            return answer

        facts = self.search.search(message)
        if facts:
            answer = self._llm_answer(message, "\n".join(facts))
            self.conversation.add(message, answer)
            self.memory.remember("User: " + message + "\nNova: " + answer)
            return answer

        internet = self.internet.search(message)
        if internet and "couldn't find" not in internet.lower():
            answer = self._llm_answer(message, internet)
            self.conversation.add(message, answer)
            self.memory.remember("User: " + message + "\nNova: " + answer)
            return answer

        answer = self.skills.execute(intent, "I couldn't find anything.", message)
        self.conversation.add(message, answer)
        self.memory.remember("User: " + message + "\nNova: " + answer)
        return answer
