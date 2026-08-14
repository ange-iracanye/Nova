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

    def reply(

        self,

        message

    ):

        message = message.strip()

        last = self.conversation.last()

        self.profile.add_question()

        intent = self.intent.detect(message)

        answer = self.calc.solve(message)

        if answer:

            self.conversation.add(

                message,

                answer

            )

            self.memory.remember(

                "User: " + message +
                "\nNova: " + answer

            )

            return answer

        facts = self.search.search(message)

        if facts:

            context = "\n".join(facts)

            answer = self.llm.answer(

                question=message,

                knowledge=context

            )

            self.conversation.add(

                message,

                answer

            )

            self.memory.remember(

                "User: " + message +
                "\nNova: " + answer

            )

            return answer

        internet = self.internet.search(

            message

        )

        if internet and "couldn't find" not in internet.lower():

            answer = self.llm.answer(

                question=message,

                knowledge=internet

            )

            self.conversation.add(

                message,

                answer

            )

            self.memory.remember(

                "User: " + message +
                "\nNova: " + answer

            )

            return answer

        answer = self.skills.execute(

            intent,

            "I couldn't find anything.",

            message

        )

        self.conversation.add(

            message,

            answer

        )

        self.memory.remember(

            "User: " + message +
            "\nNova: " + answer

        )

        return answer