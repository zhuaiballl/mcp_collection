import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import os
from nltk.stem import WordNetLemmatizer
import nltk

# 下载必要的NLTK资源
nltk.download('wordnet', quiet=True)

# 1. 加载数据
def load_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"错误: 文件 {file_path} 不是有效的 JSON")
        return []

# 2. 提取分类和描述
def extract_categories_and_descriptions(servers):
    categories = []
    descriptions = []
    for server in servers:
        # 提取分类
        if 'categories' in server and server['categories']:
            categories.extend(server['categories'])
        # 提取描述
        if 'description' in server and server['description']:
            descriptions.append(server['description'])
    return categories, descriptions

# 3. 统计原始分类
def count_original_categories(categories):
    category_count = defaultdict(int)
    for cat in categories:
        category_count[cat] += 1
    return sorted(category_count.items(), key=lambda x: x[1], reverse=True)

# 4. 主题建模与聚类
def topic_modeling(descriptions, num_topics=10):
    # 使用 TF-IDF 向量化
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X_tfidf = vectorizer.fit_transform(descriptions)

    # KMeans 聚类
    kmeans = KMeans(n_clusters=num_topics, random_state=42)
    cluster_labels = kmeans.fit_predict(X_tfidf)

    # 提取每个聚类的关键词
    def get_cluster_keywords(kmeans, vectorizer, top_n=3):
        cluster_keywords = {}
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
        terms = vectorizer.get_feature_names_out()
        for i in range(kmeans.n_clusters):
            top_terms = [terms[ind] for ind in order_centroids[i, :top_n]]
            # 使用更有意义的标签格式
            cluster_keywords[f"cluster_{i+1}"] = " ".join(top_terms)
        return cluster_keywords

    cluster_keywords = get_cluster_keywords(kmeans, vectorizer)
    return cluster_keywords, X_tfidf, vectorizer

# 5. 文本预处理 - 词形还原
def preprocess_text(text):
    lemmatizer = WordNetLemmatizer()
    words = text.lower().split()
    return [lemmatizer.lemmatize(word) for word in words]

# 6. 自动分类映射
def auto_category_mapping(original_categories, cluster_keywords, vectorizer, original_category_counts):
    # 1. 构建标准分类体系（确保包含所有聚类关键词）
    standard_categories = list(cluster_keywords.values())

    # 添加高频原始分类（出现次数超过阈值的）
    freq_threshold = 30  # 降低阈值以包含更多原始分类
    for cat, count in original_category_counts:
        if count > freq_threshold and cat not in standard_categories:
            standard_categories.append(cat)

    # 2. 为所有分类生成词向量
    all_categories = list(set(original_categories))
    try:
        category_vectors = vectorizer.transform(all_categories)
        std_vectors = vectorizer.transform(standard_categories)
    except ValueError:
        # 如果 vectorizer 没有词汇表，重新训练
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        vectorizer.fit(all_categories + standard_categories)
        category_vectors = vectorizer.transform(all_categories)
        std_vectors = vectorizer.transform(standard_categories)

    # 3. 自动映射
    category_mapping = {}
    # 为聚类关键词设置更低的阈值
    cluster_threshold = 0.15  # 降低阈值提高聚类关键词映射率
    # 为原始分类设置更高的阈值
    original_threshold = 0.5

    # 预处理聚类关键词，提取词干
    cluster_keywords_processed = {}
    for cluster_id, cluster_keyword in cluster_keywords.items():
        cluster_keywords_processed[cluster_id] = preprocess_text(cluster_keyword)

    for i, cat in enumerate(all_categories):
        # 预处理当前分类
        cat_processed = preprocess_text(cat)

        # 1. 首先尝试直接匹配聚类关键词
        matched_cluster = None
        for cluster_id, cluster_words in cluster_keywords_processed.items():
            # 如果分类和聚类关键词有共同词干，则匹配
            if any(word in cat_processed for word in cluster_words):
                matched_cluster = cluster_keywords[cluster_id]
                break

        if matched_cluster:
            category_mapping[cat] = matched_cluster
            continue

        # 2. 计算与标准分类的相似度
        similarities = cosine_similarity(category_vectors[i:i+1], std_vectors)[0]

        # 找到最相似的标准分类
        most_similar_idx = similarities.argmax()
        most_similar_score = similarities[most_similar_idx]
        most_similar_cat = standard_categories[most_similar_idx]

        # 检查是否是聚类关键词
        is_cluster = most_similar_cat in cluster_keywords.values()

        # 根据分类类型应用不同阈值
        if is_cluster and most_similar_score > cluster_threshold:
            category_mapping[cat] = most_similar_cat
        elif not is_cluster and most_similar_score > original_threshold:
            category_mapping[cat] = most_similar_cat
        else:
            # 如果没有匹配，尝试映射到最相关的聚类关键词
            # 找到与聚类关键词的最高相似度
            cluster_indices = [i for i, cat in enumerate(standard_categories) if cat in cluster_keywords.values()]
            if cluster_indices:
                cluster_similarities = similarities[cluster_indices]
                max_cluster_idx = cluster_similarities.argmax()
                max_cluster_score = cluster_similarities[max_cluster_idx]
                if max_cluster_score > cluster_threshold:
                    category_mapping[cat] = standard_categories[cluster_indices[max_cluster_idx]]
                    continue
            # 如果仍没有匹配，保留原始分类
            category_mapping[cat] = cat

    # 4. 聚合相同映射的分类
    aggregated_mapping = defaultdict(list)
    for cat, mapped_cat in category_mapping.items():
        aggregated_mapping[mapped_cat].append(cat)

    # 确保所有聚类关键词都在映射结果中
    for cluster_keyword in cluster_keywords.values():
        if cluster_keyword not in aggregated_mapping:
            aggregated_mapping[cluster_keyword] = []

    return dict(aggregated_mapping), category_mapping

# 7. 可视化分类分布
def visualize_category_distribution(category_mapping, output_file='category_distribution.png'):
    # 统计映射后的分类分布
    mapped_counts = defaultdict(int)
    for mapped_cat in category_mapping.values():
        mapped_counts[mapped_cat] += 1

    # 取前 20 个最常见的分类
    top_categories = sorted(mapped_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    categories, counts = zip(*top_categories)

    # 绘制柱状图
    plt.figure(figsize=(12, 8))
    sns.barplot(x=list(counts), y=list(categories))
    plt.title('Top 20 Category Distribution After Mapping')
    plt.xlabel('Count')
    plt.ylabel('Category')
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"分类分布图已保存到 {output_file}")

# 主函数
def main():
    # 加载服务器数据
    servers = load_data('metadata/servers/merged_servers.json')
    if not servers:
        print("没有找到有效的服务器数据，程序退出。")
        return

    # 提取分类和描述
    categories, descriptions = extract_categories_and_descriptions(servers)
    if not categories:
        print("没有找到分类数据，程序退出。")
        return

    # 统计原始分类
    original_category_counts = count_original_categories(categories)
    print("原始分类统计 (前20名):")
    for cat, count in original_category_counts[:20]:
        print(f"{cat}: {count}")

    # 主题建模
    print("\n基于描述文本的主题建模...")
    num_topics = 10  # 可调整
    cluster_keywords, X_tfidf, vectorizer = topic_modeling(descriptions, num_topics)

    print("\n发现的潜在主题 (关键词):")
    for topic, keywords in cluster_keywords.items():
        print(f"{topic}: {keywords}")

    # 自动分类映射
    print("\n自动生成分类映射...")
    aggregated_mapping, category_mapping = auto_category_mapping(
        categories, cluster_keywords, vectorizer, original_category_counts
    )

    # 保存分类映射
    mapping_file = 'category_mapping_automated.json'
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(aggregated_mapping, f, ensure_ascii=False, indent=2)
    print(f"\n分类映射已自动保存到 {mapping_file}")

    # 可视化分类分布
    visualize_category_distribution(category_mapping)

    # 统计映射到聚类关键词的比例
    cluster_count = 0
    for mapped_cat in category_mapping.values():
        if mapped_cat in cluster_keywords.values():
            cluster_count += 1
    total = len(category_mapping)
    print(f"\n映射到聚类关键词的分类比例: {cluster_count}/{total} ({cluster_count/total*100:.2f}%)")

    print("\n完全自动化分类映射完成！建议检查结果并根据需要手动调整映射。")

if __name__ == '__main__':
    main()