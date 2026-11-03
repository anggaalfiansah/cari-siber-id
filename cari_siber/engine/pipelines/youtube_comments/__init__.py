from cari_siber.engine.core.exceptions import PipelineError
"""
==============================================================================
PAKET PIPELINE YOUTUBE COMMENTS - src/pipelines/youtube_comments/
==============================================================================
Berisi modul-modul pipeline end-to-end (Langkah 0 s/d 7) untuk menganalisis
komentar dari sebuah video YouTube:
  - pipeline_scrape      : Langkah 0 - Scraping komentar & metadata video YouTube
  - pipeline_topic       : Langkah 1 - Topic Modeling BERTopic + IndoBERT
  - pipeline_label       : Langkah 2 - Pelabelan topik & sentimen berbasis AI
  - pipeline_aggregation : Langkah 3 - Agregasi komentar & penilaian confidence
  - pipeline_analysis    : Langkah 4 - Analisis engagement, likes, hearts & balasan
  - pipeline_eda         : Langkah 5 - Statistik ringkasan Exploratory Data Analysis
  - pipeline_visualize   : Langkah 6 - Pembuatan 8 grafik visualisasi PNG
  - pipeline_narrate     : Langkah 7 - Pembuatan laporan narasi insight AI
==============================================================================
"""
