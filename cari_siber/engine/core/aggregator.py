"""
==============================================================================
CORE AGGREGATOR (UNIVERSAL)
==============================================================================
Modul ini berisi fungsi-fungsi pengolahan data (Pandas murni) untuk
menggabungkan hasil pemodelan topik, pelabelan AI, dan metadata asli.
Tidak mengetahui soal nama file spesifik, platform asal, atau daftar sentimen.
Bisa dipakai secara universal (untuk ulasan Play Store, TikTok, dll).
==============================================================================
"""

import pandas as pd
import numpy as np


def merge_topics_and_labels(df_mapping: pd.DataFrame, df_labels: pd.DataFrame, topic_id_col: str = 'topic_id') -> pd.DataFrame:
    """
    Menggabungkan dataframe pemetaan topik (mapping) dengan label hasil klasifikasi AI.
    """
    # Pastikan tipe kolom topic_id sama
    if topic_id_col in df_mapping.columns and topic_id_col in df_labels.columns:
        df_mapping[topic_id_col] = df_mapping[topic_id_col].astype(str)
        df_labels[topic_id_col] = df_labels[topic_id_col].astype(str)
        
    cols_to_use = [topic_id_col] + [c for c in ['threat_domain', 'business_category', 'sub_issue', 'merge_group'] if c in df_labels.columns]
    df_labels_subset = df_labels[cols_to_use]
    
    return pd.merge(df_mapping, df_labels_subset, on=topic_id_col, how='left')


def merge_with_metadata(df_topic_mapped: pd.DataFrame, df_raw: pd.DataFrame, id_col: str, sentiment_label: str = None) -> pd.DataFrame:
    """
    Menggabungkan hasil topik yang sudah berlabel dengan dataset mentah/metadata awal.
    """
    # Hapus konten duplikat jika df_raw membawa kolom 'content' (karena df_topic_mapped biasanya sudah bawa)
    df_raw_subset = df_raw.drop(columns=['content'], errors='ignore')
    
    # Pastikan tipe kolom ID sama
    if id_col in df_topic_mapped.columns and id_col in df_raw_subset.columns:
        df_topic_mapped[id_col] = df_topic_mapped[id_col].astype(str)
        df_raw_subset[id_col] = df_raw_subset[id_col].astype(str)
        
    df_merged = pd.merge(df_topic_mapped, df_raw_subset, on=id_col, how='left')
    
    if sentiment_label:
        df_merged['sentiment'] = sentiment_label
        
    return df_merged


def calculate_confidence_level(df: pd.DataFrame, prob_col: str = 'main_topic_prob', topic_id_col: str = 'topic_id') -> pd.Series:
    """
    Menghitung tingkat kepercayaan model terhadap klasifikasi (High/Medium/Low) secara vectorized.
    """
    if df.empty:
        return pd.Series(dtype=object)

    probs = pd.to_numeric(df.get(prob_col, 0.0), errors="coerce").fillna(0.0)
    topics = df.get(topic_id_col, "")
    is_outlier = topics.astype(str).isin(["-1", "-1.0"])

    cond_high = (~is_outlier) & (probs >= 0.7)
    cond_medium = (~is_outlier) & (probs >= 0.5)

    choices = ["High", "Medium"]
    res = np.select([cond_high, cond_medium], choices, default="Low")
    return pd.Series(res, index=df.index)


def generate_category_summary(df: pd.DataFrame, group_cols: list, score_col: str = None) -> pd.DataFrame:
    """
    Membuat dataframe ringkasan agregat dari kelompok kategori (misal: per sentimen dan per business_category).
    """
    summary_data = []
    
    # Isi null value dengan string kosong agar groupby tidak drop row-nya
    for col in group_cols:
        if col in df.columns:
            df[col] = df[col].fillna('')
            
    grouped = df.groupby(group_cols)
    
    for name, group in grouped:
        if len(group_cols) == 1:
            row_dict = {group_cols[0]: name}
        else:
            row_dict = dict(zip(group_cols, name))
            
        review_count_all = len(group)
        
        if 'confidence_level' in group.columns:
            confident_group = group[group['confidence_level'].isin(['High', 'Medium'])]
            review_count_confident = len(confident_group)
        else:
            review_count_confident = review_count_all
            
        share_confident = (review_count_confident / review_count_all) if review_count_all > 0 else 0.0
        
        if score_col and score_col in group.columns:
            avg_score = group[score_col].mean()
            row_dict['avg_score'] = round(avg_score, 2)
            
        if 'sub_issue' in group.columns:
            valid_issues = group['sub_issue'].dropna().astype(str).str.strip()
            valid_issues = valid_issues[valid_issues != '']
            if len(valid_issues) > 0:
                top_3 = valid_issues.value_counts().head(3).index.tolist()
                example_sub_issues = ", ".join(top_3)
            else:
                example_sub_issues = ""
            row_dict['example_sub_issues'] = example_sub_issues
            
        row_dict.update({
            'review_count_all': review_count_all,
            'review_count_confident': review_count_confident,
            'share_confident': round(share_confident, 4)
        })
        
        summary_data.append(row_dict)
        
    df_summary = pd.DataFrame(summary_data)
    if not df_summary.empty:
        sort_cols = [group_cols[0], 'review_count_all'] if len(group_cols) > 0 else ['review_count_all']
        sort_asc = [True, False] if len(group_cols) > 0 else [False]
        
        # Validasi kolom sortir eksis
        sort_cols_actual = [c for c in sort_cols if c in df_summary.columns]
        sort_asc_actual = sort_asc[:len(sort_cols_actual)]
        
        if sort_cols_actual:
            df_summary = df_summary.sort_values(by=sort_cols_actual, ascending=sort_asc_actual)
            
    return df_summary
