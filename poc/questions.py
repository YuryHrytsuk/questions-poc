import typing
from typing import Dict, Any, Optional, Tuple, Union, Set, cast

Choices = Union[typing.List[str], Tuple[str, Any]]
Answers = Dict[str, Any]


class Config:
    def __init__(
            self,
            sections: Tuple["Section"],
            use_defaults: bool = False,
    ):
        self._validate_dependencies(sections)

        self.use_defaults = use_defaults
        self._sections = sections
        self._answers = {section.name: section.answers for section in self.sections}

        self._assign_config_to_sections(sections)

    @property
    def sections(self) -> Tuple["Section"]:
        return self._sections

    @property
    def answers(self) -> Answers:
        return self._answers

    def get_answer_of(self, question: "Question") -> Any:
        section = question.section
        if section not in self.sections:
            raise ValueError(f"{question} doesn't belong to {self}")

        return section.get_answer_of(question)

    @staticmethod
    def _validate_dependencies(sections: Tuple["Section"]) -> None:
        validated = {section: cast(typing.List["Question"], []) for section in sections}

        for section in sections:
            for question in section.questions:
                for dependency in question.dependencies:
                    if dependency not in validated[dependency.section]:
                        raise ValueError(f"Unresolved {dependency=} of {question}")

                validated[question.section].append(question)

    def _assign_config_to_sections(self, sections: Tuple["Section", ...]) -> None:
        for section in sections:
            section.config = self


class Section:
    def __init__(
        self,
        name: str,
        questions: Tuple["Question", ...],
        use_defaults: Optional[bool] = None,
        answers: Optional[Answers] = None,
    ):
        self._validate_questions(questions)

        if answers is None:
            answers: Answers = {}

        self.name = name
        self.answers = answers
        self._use_defaults = use_defaults
        self._questions = questions
        self._config: Optional[Config] = None
        self._assign_section_to_questions(questions)

    @property
    def config(self) -> Config:
        if self._config is None:
            raise RuntimeError("'config' is not initialized")

        return self._config

    @config.setter
    def config(self, value: Config) -> None:
        if self._config is not None:
            raise ValueError("'config' can be set only once")

        self._config = value

    @property
    def questions(self) -> Tuple["Question", ...]:
        return self._questions

    @property
    def use_defaults(self) -> bool:
        if self._use_defaults is not None:
            return self._use_defaults

        return self.config.use_defaults

    def _assign_section_to_questions(self, questions) -> None:
        for question in questions:
            question.section = self

    @staticmethod
    def _validate_questions_have_unique_names(questions: Tuple["Question", ...]) -> None:
        unique_names: Set[str] = set()

        for question in questions:
            if question.name in unique_names:
                raise ValueError(f"Duplicate question name '{question.name}'")

            unique_names.add(question.name)

    def _validate_questions(self, questions: Tuple["Question", ...]) -> None:
        self._validate_questions_have_unique_names(questions)

    def get_answer_of(self, question: "Question") -> Any:
        if question not in self.questions:
            raise ValueError(f"{question} doesn't belong to the {self}")

        return self.answers[question.name]


class Question:
    name: str
    message: str = ""
    choices: Optional[Choices] = None
    default: Optional[Any] = None
    show_default: bool = True

    @property
    def ignore(self) -> bool:
        if self.default is None:
            return False

        return self.section.use_defaults

    def validate(self, value) -> bool:
        return True

    def __init__(self, dependencies: Tuple["Question", ...] = ()):
        if not hasattr(self, "name"):
            raise TypeError("'name' is not initialized")
        if self.name == "":
            raise ValueError("'name' can't be empty string")

        self._section: Optional[Section] = None
        self.dependencies = dependencies

    @property
    def section(self) -> Section:
        if self._section is None:
            raise RuntimeError("'section' is not initialized")

        return self._section

    @section.setter
    def section(self, value: Section) -> None:
        if self._section is not None:
            raise ValueError("'section' can be set only once")

        self._section = value

    def resolve_dependency(self, dependency: "Question") -> Any:
        return self.section.config.get_answer_of(dependency)


class Text(Question):
    kind = 'text'

    default: Optional[str] = None


class Password(Text):
    kind = 'password'

    echo: str = '*'


class Editor(Text):
    kind = 'editor'


class Confirm(Question):
    kind = 'confirm'

    default: Optional[bool] = None


class List(Question):
    kind = 'list'

    carousel: bool = False


class Checkbox(Question):
    kind = 'checkbox'
