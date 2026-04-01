from typing import List, Tuple
import dspy
from pydantic import BaseModel, Field


class ExtractedConceptSchema(BaseModel):
    pref_label: str = Field(description="The preferred name of the concept")
    alt_labels: List[str] = Field(description="Synonyms or alternate names")
    definition: str = Field(description="A concise definition of the concept")
    broader_than: List[str] = Field(
        description="Preferred labels of broader or parent concepts"
    )
    narrower_than: List[str] = Field(
        description="Preferred labels of narrower or child concepts"
    )
    related_to: List[str] = Field(description="Preferred labels of related concepts")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")


class ExtractedGraph(BaseModel):
    concepts: List[ExtractedConceptSchema] = Field(
        description="List of extracted SKOS concepts"
    )
    relations: List[Tuple[str, str, str]] = Field(
        description=(
            "List of raw relationships as (subject, predicate, object) tuples where "
            "subject and object are concept preferred labels"
        )
    )


class ExtractConceptGraphSignature(dspy.Signature):
    """
    Extract a SKOS-style concept graph from source text.
    """

    text: str = dspy.InputField(desc="Source text to analyze.")
    extracted_graph: ExtractedGraph = dspy.OutputField()


class GroundedAnswerSignature(dspy.Signature):
    """
    Answer a question using only the supplied graph context.
    If the context is insufficient, state that directly.
    """

    question: str = dspy.InputField(desc="User question to answer.")
    graph_context: str = dspy.InputField(
        desc="Knowledge-graph facts and definitions that must ground the answer."
    )
    answer: str = dspy.OutputField(desc="Grounded answer using only graph_context.")


class ConceptGraphExtractor(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.predict = dspy.Predict(ExtractConceptGraphSignature)


class GroundedAnswerGenerator(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.predict = dspy.Predict(GroundedAnswerSignature)

    def forward(self, question: str, graph_context: str) -> str:
        prediction = self.predict(question=question, graph_context=graph_context)
        return prediction.answer
