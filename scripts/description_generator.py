"""
Text description generator for book-selling posts.
Generates viral-style descriptions based on proven templates from top-performing posts.
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional


# Proven viral hook templates extracted from top-performing posts
HOOK_TEMPLATES = [
    "还在死{pain}？{year}年绝版老书《{book}》，专门治好{problem}！",
    "🔥别再{pain}了！这本{era}的神书把{subject}讲透了📖",
    "以前的{subject}教材长这个样子！真的是太适合自学了！讲的明明白白！",
    "{era}年绝版老书《{book}》{author}老师的\"速成记忆法\"，当年无数人靠它摸透{subject}底层逻辑，告别{pain}！",
    "对比新旧教材才看懂，老书讲课足够有耐心，一步一步推进，生怕孩子跟不上进度。",
    "老教材：可以自学。新教材：你休想！它能慢慢地把每个知识点讲透，因为它生怕孩子学不会听不懂！",
    "老教材才是真的想把孩子教会！老教材是可以拿来给孩子自学就会的！魅力太大了",
    "有没有发现老教材把每个题都讲得很透",
]

# Selling point templates
SELLING_POINT_TEMPLATES = [
    "不讲空话，不堆词表，把{subject}的核心规律，编成{count}条口诀，好懂又好记",
    "从{topic1}、{topic2}，到{topic3}、{topic4}，全是能直接落地的干货",
    "自带例句+配套练习，当年没有网课的年代，这就是无数自学者的\"私教\"",
    "全书{author}老师总结{count}条核心规律，中英对照，配口诀、例句、练习题带完整答案",
    "学生补语法、零基础自学、大人改写作全都合适",
    "不用死记硬背，看懂长难句、写地道英文轻松很多",
    "早年老教师手写梳理干货，现在完整版很难找，想踏踏实实学好{subject}一定要收！",
]

# Hashtag pools by subject
HASHTAG_POOLS = {
    '英语': [
        '#老英语学习资料分享', '#零基础学英语', '#老英语教材',
        '#语法学霸笔记', '#英语怎么学', '#英语语法',
        '#好书分享', '#知识分享', '#干货分享', '#成长',
        '#英语', '#英语小达人', '#零基础英语', '#小学英语',
        '#王克谦英语', '#英语的基本规律', '#绝版英语老书',
        '#英语底层逻辑', '#告别中式英语', '#自学英语干货',
    ],
    '数学': [
        '#老教材', '#小学数学', '#数学启蒙', '#数学基础',
        '#绝版老书', '#好书分享', '#知识分享', '#干货分享',
    ],
    '通用': [
        '#好书分享', '#知识分享', '#干货分享', '#成长',
        '#老教材', '#绝版老书', '#自学', '#学习方法',
    ],
}


def generate_description(
    book_name: str,
    page_analyses: List[Dict],
    config: Optional[Dict] = None
) -> str:
    """
    Generate a viral-style text description for the book post.

    Args:
        book_name: Name of the book.
        page_analyses: List of analysis dicts from vision analysis.
        config: Optional config with author, year, subject, pain_points.

    Returns:
        Complete text description with hashtags.
    """
    if config is None:
        config = {}

    # Extract info from config or use defaults
    author = config.get('author', '王克谦')
    year = config.get('year', '1984')
    subject = config.get('subject', '英语')
    pain = config.get('pain', '死记硬背')
    era = config.get('era', '80年代')
    problem = config.get('problem', '中式英语')

    # Extract topics from page analyses
    topics = []
    for analysis in page_analyses:
        topic = analysis.get('page_topic', '')
        key = analysis.get('key_text', '')[:30]
        if topic:
            topics.append(topic)
        if key and key != topic:
            topics.append(key)

    # Deduplicate and limit
    unique_topics = list(dict.fromkeys(topics))[:6]

    # Subject-specific short name for templates
    subject_short_map = {
        '英语': '英语', '数学': '数学', '语文': '语文', '文言': '文言文',
        '物理': '物理', '化学': '化学', '通用': '学习',
    }
    subject_short = subject_short_map.get(subject, subject)

    # Build the description
    lines = []

    # Opening hook
    hook = f"以前的{subject}教材长这个样子！真的是太适合自学了！讲的明明白白！"
    lines.append(hook)
    lines.append("")

    # Book intro
    lines.append(f"{year}年绝版老书《{book_name}》")
    lines.append(f"{author}老师的\"速成记忆法\"，当年无数人靠它摸透{subject_short}底层逻辑，告别死记硬背！")

    # Selling points
    lines.append(f"不讲空话，不堆词表，把{subject_short}的核心规律，编成口诀，好懂又好记")

    # Content coverage from actual analysis
    if unique_topics:
        topic_str = "、".join(unique_topics[:4])
        lines.append(f"涵盖{topic_str}，全是能直接落地的干货")
    else:
        lines.append(f"涵盖{subject}核心知识点，全是能直接落地的干货")

    lines.append("自带例句+配套练习，当年没有网课的年代，这就是无数自学者的\"私教\"")

    # Hashtags
    tag_pool = HASHTAG_POOLS.get(subject, HASHTAG_POOLS['通用'])
    # Always include book-specific tags
    book_tag = f"#{book_name}"
    tags = [book_tag] + tag_pool[:12]
    lines.append("")
    lines.append(" ".join(tags))

    return "\n".join(lines)


def generate_description_ai(
    book_name: str,
    page_analyses: List[Dict],
    config: Optional[Dict] = None
) -> str:
    """
    Use AI (vision model) to generate a more nuanced description.
    Falls back to template-based generation if API fails.
    """
    if config is None:
        config = {}

    api_base = os.environ.get('VISION_API_URL', '')
    api_key = os.environ.get('VISION_API_KEY', '')
    model = os.environ.get('VISION_MODEL', 'mimo-v2.5-pro')

    if not api_base or not api_key:
        print("[desc] No vision API configured, using template-based generation")
        return generate_description(book_name, page_analyses, config)

    # Build context from analyses
    topics_summary = []
    for a in page_analyses:
        topic = a.get('page_topic', '')
        key = a.get('key_text', '')[:40]
        if topic:
            topics_summary.append(f"- {topic}: {key}")

    topics_text = "\n".join(topics_summary) if topics_summary else "（无分析数据）"

    author = config.get('author', '王克谦')
    year = config.get('year', '1984')
    subject = config.get('subject', '英语')

    prompt = f"""你是一个视频号爆款文案写手。根据以下信息，写一段图书带货的图文描述。

书名：《{book_name}》
作者：{author}老师
年代：{year}年
学科：{subject}

书中涉及的知识点：
{topics_text}

要求：
1. 开头用一句抓人的话（可以参考这些风格："以前的教材长这个样子！""老教材才是真的想把孩子教会！""有没有发现老教材把每个题都讲得很透"）
2. 介绍书的核心卖点（不讲空话、口诀记忆、配套练习等）
3. 根据实际知识点列出书涵盖的内容
4. 语言口语化，像朋友推荐，不要AI味
5. 结尾加上话题标签，格式：#标签名
6. 总字数200-400字
7. 参考以下爆款风格但不要照抄：
   - "不讲空话，不堆词表，把核心规律编成口诀，好懂又好记"
   - "自带例句+配套练习，当年没有网课的年代，这就是无数自学者的私教"
   - "早年老教师手写梳理干货，现在完整版很难找"

请直接输出描述文本，不要加任何前缀说明。"""

    try:
        url = f"{api_base.rstrip('/')}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7
        }

        print("[desc] Generating AI description...")
        resp = requests.post(url, json=payload, headers=headers, timeout=60)

        if resp.status_code == 200:
            result = resp.json()
            content = result['choices'][0]['message']['content']
            # Clean up: remove * and empty lines
            content = content.replace('*', '')
            lines = [line for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)
            print(f"[desc] AI description generated ({len(content)} chars)")
            return content.strip()
        else:
            print(f"[desc] API returned {resp.status_code}, falling back to template")
            return generate_description(book_name, page_analyses, config)

    except Exception as e:
        print(f"[desc] AI generation failed: {e}, falling back to template")
        return generate_description(book_name, page_analyses, config)
