"""
Cover hook text generator — rule-based, subject-aware, context-driven.

Extracts patterns from proven viral titles and generates unique hooks
based on book metadata (name, author, year, subject, topics).
"""

import random
from typing import List, Dict, Optional


# ============================================================
# Pattern templates extracted from viral title analysis
# ============================================================

# Pattern 1: Generational contrast (老X vs 现在)
PATTERN_GENERATIONAL = [
    "老一辈就是真敢教",
    "老一辈才敢教真{subject_short}",
    "老一辈得多高的知识储备才能写成这本书",
    "老教材真的是太了解我们了",
    "老教材真的不会防自学",
    "老教材的扎实感现在的教材真比不了",
    "老教材真的毫无保留",
    "以前的{subject_short}书真的超敢写",
    "以前的书是真的敢教能简单绝不复杂",
    "以前{subject_short}我都是自学的",
    "几十年前的书是真想教我们{topic_keyword}",
    "原来我们被骗了这么多年",
]

# Pattern 2: Direct claim (老书就是...)
PATTERN_DIRECT = [
    "老书就是敢真教",
    "老书就是敢教真{subject_short}",
    "老书就是简单易懂",
    "老书是真的敢教",
    "老书就是会教把{topic_detail}",
    "经典老书从不弯弯绕绕",
    "这才是人民的教材简单易懂学得会",
]

# Pattern 3: Question/observation (有没有发现...)
PATTERN_QUESTION = [
    "有没有发现老教材把每个题都讲得很透",
    "有没有发现老教材是真的想把孩子教会",
    "有没有发现老教材真的毫无保留",
    "这样教{subject_short}{accessibility}",
    "讲真以前{subject_short}我都是自学的",
]

# Pattern 4: Personal test (我宣布...)
PATTERN_TESTIMONIAL = [
    "我宣布这本书是我{audience}{subject_short}开窍的神",
    "我宣布这是我{audience}{subject_short}开窍的神",
    "一本能让{audience}看得懂的绝版教材",
]

# Pattern 5: Authority + topic (钱学森/作者+核心内容)
PATTERN_AUTHORITY = [
    "{author}{topic_keyword}精髓",
    "{author}{topic_keyword}天花板",
    "{author}的顶级思想",
]

# Pattern 6: Year + claim
PATTERN_YEAR = [
    "{year}年出版老书就是敢教真东西",
    "{year}年出版老教材才是真的教书育人",
]

# Pattern 7: Emotional revelation
PATTERN_EMOTIONAL = [
    "感觉以前的书才是真的教书育人",
    "怪不得老一辈{subject_short}功底扎实",
]


# ============================================================
# Subject-specific keyword mappings
# ============================================================

SUBJECT_KEYWORDS = {
    '英语': {
        'subject_short': '英语',
        'topic_keywords': ['语法', '句子结构', '阅读', '词汇', '写作', '口语'],
        'topic_details': [
            '复杂语法讲得明明白白',
            '句子结构拆解得清清楚楚',
            '语法规律编成好记的口诀',
            '每个语法点都配例句和练习',
        ],
        'audiences': ['小学儿子', '女儿', '初中生', '高中生', '大学生'],
        'accessibility': '你是不是也能学会了',
    },
    '数学': {
        'subject_short': '数学',
        'topic_keywords': ['解题', '公式', '定理', '几何', '代数', '函数'],
        'topic_details': [
            '解题思路拆解得明明白白',
            '每个公式都讲透原理',
            '难题变成简单题',
            '几何代数全覆盖',
        ],
        'audiences': ['小学儿子', '女儿', '初中生', '高中生'],
        'accessibility': '你是不是也能开窍了',
    },
    '语文': {
        'subject_short': '语文',
        'topic_keywords': ['阅读', '作文', '古诗', '文言文', '修辞', '阅读理解'],
        'topic_details': [
            '阅读理解讲得透透的',
            '作文思路拆解得明明白白',
            '古诗文逐字逐句讲透',
        ],
        'audiences': ['小学儿子', '女儿', '初中生'],
        'accessibility': '你是不是也能写好作文了',
    },
    '文言': {
        'subject_short': '文言文',
        'topic_keywords': ['文言语法', '实词虚词', '古今异义', '词类活用', '特殊句式'],
        'topic_details': [
            '文言语法讲得明明白白',
            '每个实词虚词都讲透',
            '古今异义对比清晰',
        ],
        'audiences': ['初中生', '高中生', '学生'],
        'accessibility': '你是不是也能看懂古文了',
    },
    '物理': {
        'subject_short': '物理',
        'topic_keywords': ['力学', '电学', '光学', '公式推导', '实验原理'],
        'topic_details': [
            '力学原理讲得透透的',
            '每个公式都推导清楚',
            '实验步骤拆解明白',
        ],
        'audiences': ['初中生', '高中生', '理科生'],
        'accessibility': '你是不是也能搞懂物理了',
    },
    '化学': {
        'subject_short': '化学',
        'topic_keywords': ['化学方程式', '元素周期', '有机化学', '实验', '反应原理'],
        'topic_details': [
            '化学方程式讲得明明白白',
            '每个反应原理都讲透',
            '实验步骤拆解清楚',
        ],
        'audiences': ['初中生', '高中生', '理科生'],
        'accessibility': '你是不是也能学好化学了',
    },
}

# Default for unknown subjects
SUBJECT_DEFAULT = {
    'subject_short': '学习',
    'topic_keywords': ['基础知识', '核心规律', '重点难点', '学习方法'],
    'topic_details': [
        '核心知识点讲得明明白白',
        '每个重点都配例题和练习',
        '基础规律编成好记的口诀',
    ],
    'audiences': ['学生', '孩子', '自学者'],
    'accessibility': '你是不是也能学会了',
}


def generate_hook_text(
    book_name: str,
    author: str = '',
    year: str = '',
    subject: str = '通用',
    page_topics: List[str] = None,
    used_hooks: List[str] = None,
    seed: int = None
) -> str:
    """
    Generate a unique, context-aware hook text for the book cover.

    Args:
        book_name: Name of the book.
        author: Author name.
        year: Publication year.
        subject: Subject (英语/数学/语文/文言/物理/化学/通用).
        page_topics: List of page topics from vision analysis.
        used_hooks: List of previously used hooks (to avoid repetition).
        seed: Random seed for reproducibility (None = random).

    Returns:
        Hook text string.
    """
    if used_hooks is None:
        used_hooks = []
    if page_topics is None:
        page_topics = []

    # Get subject config
    subject_config = SUBJECT_KEYWORDS.get(subject, SUBJECT_DEFAULT)

    # Extract topic keyword from page topics
    topic_keyword = _extract_topic_keyword(page_topics, subject_config)

    # Build variable substitutions
    variables = {
        'subject_short': subject_config['subject_short'],
        'topic_keyword': topic_keyword,
        'topic_detail': random.choice(subject_config['topic_details']),
        'author': author[:4] if author else '',  # Limit author name length
        'year': year,
        'audience': random.choice(subject_config['audiences']),
        'accessibility': subject_config['accessibility'],
    }

    # Collect all pattern templates
    all_patterns = (
        PATTERN_GENERATIONAL +
        PATTERN_DIRECT +
        PATTERN_QUESTION +
        PATTERN_TESTIMONIAL +
        PATTERN_YEAR +
        PATTERN_EMOTIONAL
    )

    # Filter out patterns that require missing variables
    valid_patterns = []
    for p in all_patterns:
        try:
            p.format(**variables)
            valid_patterns.append(p)
        except (KeyError, IndexError):
            continue

    # Filter out previously used hooks
    available = [p for p in valid_patterns if p.format(**variables) not in used_hooks]
    if not available:
        available = valid_patterns  # Reset if all used

    # Select and format
    if seed is not None:
        random.seed(seed)

    template = random.choice(available)
    hook = template.format(**variables)

    return hook


def _extract_topic_keyword(page_topics: List[str], subject_config: Dict) -> str:
    """Extract a relevant topic keyword from page analysis topics."""
    if not page_topics:
        return random.choice(subject_config['topic_keywords'])

    # Try to find a subject-specific keyword in the topics
    for topic in page_topics:
        for keyword in subject_config['topic_keywords']:
            if keyword in topic:
                return keyword

    # Fallback: use the first topic's key phrase
    if page_topics:
        # Extract the core phrase (first 4-6 chars)
        topic = page_topics[0]
        if len(topic) > 6:
            return topic[:6]
        return topic

    return random.choice(subject_config['topic_keywords'])


def generate_unique_hooks(
    book_name: str,
    author: str = '',
    year: str = '',
    subject: str = '通用',
    page_topics: List[str] = None,
    count: int = 5
) -> List[str]:
    """
    Generate multiple unique hook texts for A/B testing.

    Args:
        book_name: Name of the book.
        author: Author name.
        year: Publication year.
        subject: Subject.
        page_topics: List of page topics.
        count: Number of unique hooks to generate.

    Returns:
        List of unique hook text strings.
    """
    hooks = []
    used = []

    for i in range(count * 3):  # Try up to 3x to get unique hooks
        hook = generate_hook_text(
            book_name=book_name,
            author=author,
            year=year,
            subject=subject,
            page_topics=page_topics,
            used_hooks=used,
            seed=hash(f"{book_name}_{i}") % 10000
        )
        if hook not in hooks:
            hooks.append(hook)
            used.append(hook)
        if len(hooks) >= count:
            break

    return hooks
