from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Category:
    task_type: str
    remark: str


CATEGORIES = {
    "embedding": Category("Embedding / Retrieval", "文本向量/Embedding模型，用于语义搜索、文本相似度、聚类和RAG检索。"),
    "reranker": Category("Reranker / Ranking", "重排序模型，用于搜索和RAG中的候选文档相关性排序。"),
    "llm": Category("LLM / Text Generation", "文本生成/对话类大语言模型，用于问答、写作、代码或指令跟随。"),
    "code": Category("Code", "代码模型，用于代码生成、补全、理解或代码检索。"),
    "multimodal": Category("Multimodal / Vision-Language", "多模态/视觉语言模型，用于图文理解、OCR、图片问答或图文生成。"),
    "image_generation": Category("Diffusion / Image Generation", "图像生成模型，用于文生图、图像编辑或生成式视觉任务。"),
    "depth": Category("Vision / Depth Estimation", "深度估计视觉模型，用于从图像预测深度或三维结构。"),
    "vision": Category("Vision / Image Understanding", "计算机视觉模型，用于图像识别、检测、分割或视觉特征提取。"),
    "audio": Category("Audio / Speech", "语音/音频模型，用于语音识别、语音合成、音频分类或音频理解。"),
    "timeseries": Category("Time Series / Forecasting", "时间序列模型，用于预测、异常检测或时序表征学习。"),
    "nlp": Category("Text Classification / NLP", "NLP理解模型，用于文本分类、实体识别、掩码预测或其他文本理解任务。"),
    "utility": Category("Utility / Infrastructure", "模型工具/基础设施项目，用于量化、格式转换、适配或部署。"),
    "other": Category("Other / Specialized", "专用或尚未明确分类的模型，建议结合模型卡进一步核实用途。"),
}

PIPELINE_TO_KEY = {
    "feature-extraction": "embedding", "sentence-similarity": "embedding", "text-ranking": "reranker",
    "text-generation": "llm", "text2text-generation": "llm", "conversational": "llm",
    "image-text-to-text": "multimodal", "visual-question-answering": "multimodal",
    "document-question-answering": "multimodal", "image-to-text": "multimodal",
    "text-to-image": "image_generation", "image-to-image": "image_generation",
    "unconditional-image-generation": "image_generation", "depth-estimation": "depth",
    "image-classification": "vision", "object-detection": "vision", "image-segmentation": "vision",
    "zero-shot-image-classification": "vision", "video-classification": "vision",
    "automatic-speech-recognition": "audio", "text-to-speech": "audio", "audio-classification": "audio",
    "audio-to-audio": "audio", "voice-activity-detection": "audio",
    "time-series-forecasting": "timeseries", "text-classification": "nlp",
    "token-classification": "nlp", "fill-mask": "nlp", "question-answering": "nlp",
    "summarization": "nlp", "translation": "nlp",
}


def classify_model(
    model_id: str, pipeline_tag: str | None = None, library_name: str | None = None,
    tags: Iterable[str] | str | None = None,
) -> Category:
    pipeline = (pipeline_tag or "").strip().lower()
    if pipeline in PIPELINE_TO_KEY:
        return CATEGORIES[PIPELINE_TO_KEY[pipeline]]
    items = tags.replace("|", ",").split(",") if isinstance(tags, str) else (tags or [])
    text = " ".join([model_id.lower(), (library_name or "").lower(), pipeline, " ".join(map(str, items)).lower()])
    rules = (
        ("reranker", ("rerank", "cross-encoder", "text-ranking")),
        ("embedding", ("sentence-transformers", "embedding", "sentence-similarity")),
        ("timeseries", ("time-series", "forecasting", "chronos", "timesfm")),
        ("image_generation", ("text-to-image", "diffusers", "stable-diffusion", "flux.1", "controlnet")),
        ("multimodal", ("vision-language", "multimodal", "image-text-to-text", "visual-question")),
        ("depth", ("depth-estimation", "unidepth", "depth-anything")),
        ("audio", ("automatic-speech-recognition", "text-to-speech", "whisper", "wav2vec", "audio")),
        ("code", ("code-generation", "coder", "codegemma", "starcoder", "codestral")),
        ("llm", ("text-generation", "causal-lm", "llama", "qwen", "mistral", "gemma", "deepseek")),
        ("vision", ("image-classification", "object-detection", "segmentation", "computer-vision", "timm")),
        ("nlp", ("text-classification", "token-classification", "fill-mask", "bert", "roberta")),
        ("utility", ("gguf", "quantized", "onnx", "adapter", "lora", "safetensors")),
    )
    return next((CATEGORIES[key] for key, tokens in rules if any(token in text for token in tokens)), CATEGORIES["other"])
