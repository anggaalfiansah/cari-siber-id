"""
==============================================================================
CORE PACKAGE — src/core/
==============================================================================
Berisi modul-modul universal yang tidak bergantung pada platform atau
format data tertentu. Dapat digunakan kembali di berbagai konteks
(pipeline Play Store, TikTok, CSV custom, dll).

Modul yang tersedia:
  - topic_modeling : train_bertopic, normalisasi_teks, get_stopwords, dll
  - ai_client      : generate_text, generate_structured_json
  - ai_labeler     : TopicClassification, BatchTopicLabels, label_csv_file
  - aggregator     : merge_topics_and_labels, merge_with_metadata, etc
==============================================================================
"""

from cari_siber.engine.core.topic_modeling import (
    load_kamus_slang,
    get_bertopic_config,
    get_stopwords,
    normalisasi_teks,
    train_bertopic,
)

from cari_siber.engine.core.ai_client import (
    generate_text,
    generate_structured_json,
)

from cari_siber.engine.core.ai_labeler import (
    TopicClassification,
    BatchTopicLabels,
    label_csv_file,
)

from cari_siber.engine.core.aggregator import (
    merge_topics_and_labels,
    merge_with_metadata,
    calculate_confidence_level,
    generate_category_summary,
)

from cari_siber.engine.core.agentic_gates import (
    AgenticAuditLogger,
    run_quality_gate,
    audit_and_heal_topic_clustering,
    verify_and_heal_topic_labels,
    reroute_low_confidence_records,
    run_report_gate,
)

__all__ = [
    # topic_modeling
    "load_kamus_slang",
    "get_bertopic_config",
    "get_stopwords",
    "normalisasi_teks",
    "train_bertopic",
    # ai_client
    "generate_text",
    "generate_structured_json",
    # ai_labeler
    "TopicClassification",
    "BatchTopicLabels",
    "label_csv_file",
    # aggregator
    "merge_topics_and_labels",
    "merge_with_metadata",
    "calculate_confidence_level",
    "generate_category_summary",
]
