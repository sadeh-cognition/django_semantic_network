import dspy

from .llm_schemas import ExtractedGraph


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
