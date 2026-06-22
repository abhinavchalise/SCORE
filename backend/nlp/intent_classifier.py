from backend.latency import counter

CLASSIFIER_INTENTS = ["deep_focus", "light_focus", "creative_flow", "calm", "sleep_aid"]
CUSTOM_INTENT = "custom"
CONFIDENCE_THRESHOLD = 0.55
ENCODER_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EPOCHS = 20
BATCH_SIZE = 16

_encoder = None
_default_classifier = None


def get_encoder():
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer

        _encoder = SentenceTransformer(ENCODER_ID)
    return _encoder


class IntentClassifier:
    def __init__(self) -> None:
        from torch import nn

        self.head = nn.Linear(EMBEDDING_DIM, len(CLASSIFIER_INTENTS))
        self.head.eval()

    def _embed(self, texts):
        import torch

        vectors = get_encoder().encode(list(texts), convert_to_numpy=True)
        return torch.tensor(vectors, dtype=torch.float32)

    def classify(self, text: str) -> tuple[str, float]:
        import torch

        with torch.no_grad():
            probabilities = torch.softmax(self.head(self._embed([text])), dim=1)[0]
        confidence, index = torch.max(probabilities, dim=0)
        confidence = confidence.item()
        if confidence < CONFIDENCE_THRESHOLD:
            counter("nlp.classify.low_confidence")
            return CUSTOM_INTENT, confidence
        return CLASSIFIER_INTENTS[index.item()], confidence

    def train(self, examples: list[dict]) -> None:
        import torch
        from torch.optim import AdamW

        features = self._embed([example["text"] for example in examples])
        labels = torch.tensor([CLASSIFIER_INTENTS.index(example["intent"]) for example in examples])
        optimizer = AdamW(self.head.parameters(), lr=1e-3)
        loss_fn = torch.nn.CrossEntropyLoss()

        self.head.train()
        for _ in range(EPOCHS):
            order = torch.randperm(len(examples))
            for start in range(0, len(examples), BATCH_SIZE):
                batch = order[start : start + BATCH_SIZE]
                optimizer.zero_grad()
                loss_fn(self.head(features[batch]), labels[batch]).backward()
                optimizer.step()
        self.head.eval()

    def evaluate(self, examples: list[dict]) -> float:
        import torch

        with torch.no_grad():
            predicted = torch.argmax(
                self.head(self._embed([example["text"] for example in examples])), dim=1
            )
        truth = [CLASSIFIER_INTENTS.index(example["intent"]) for example in examples]
        return _macro_f1(truth, predicted.tolist(), len(CLASSIFIER_INTENTS))

    def save(self, path: str) -> None:
        import torch

        torch.save(self.head.state_dict(), path)

    def load(self, path: str) -> None:
        import torch

        self.head.load_state_dict(torch.load(path))
        self.head.eval()


def classify(text: str) -> tuple[str, float]:
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = IntentClassifier()
    return _default_classifier.classify(text)


def _macro_f1(truth: list[int], predicted: list[int], num_classes: int) -> float:
    scores = []
    for label in range(num_classes):
        true_positives = sum(
            1
            for truth_label, pred_label in zip(truth, predicted)
            if truth_label == label and pred_label == label
        )
        false_positives = sum(
            1
            for truth_label, pred_label in zip(truth, predicted)
            if truth_label != label and pred_label == label
        )
        false_negatives = sum(
            1
            for truth_label, pred_label in zip(truth, predicted)
            if truth_label == label and pred_label != label
        )
        precision = (
            true_positives / (true_positives + false_positives)
            if true_positives + false_positives
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if true_positives + false_negatives
            else 0.0
        )
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores)
