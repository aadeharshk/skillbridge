"""Skills taxonomy and extractor.

Each canonical skill has aliases. Matching uses word boundaries so 'R' doesn't
match inside 'React' and 'Java' doesn't match 'JavaScript'.
"""
import re

# canonical name: (category, [aliases])
TAXONOMY: dict[str, tuple[str, list[str]]] = {
    # Programming languages
    "Python": ("Programming", ["python", "python3"]),
    "SQL": ("Programming", ["sql", "t-sql", "pl/sql", "tsql"]),
    "R": ("Programming", [r"\br\b(?![-&/])"]),
    "Java": ("Programming", [r"java(?!\s*script)"]),
    "JavaScript": ("Programming", ["javascript", "js", "es6"]),
    "TypeScript": ("Programming", ["typescript", "ts"]),
    "Scala": ("Programming", ["scala"]),
    "Go": ("Programming", ["golang"]),
    "C++": ("Programming", [r"c\+\+"]),
    "Bash": ("Programming", ["bash", "shell scripting", "shell script"]),
    "PHP": ("Programming", ["php"]),
    "HTML/CSS": ("Programming", ["html", "css", "html5", "css3"]),
    # Data engineering
    "ETL": ("Data Engineering", ["etl", "elt", "etl pipelines", "data pipelines", "data pipeline"]),
    "Apache Spark": ("Data Engineering", ["spark", "pyspark", "apache spark", "spark sql"]),
    "Apache Airflow": ("Data Engineering", ["airflow", "apache airflow"]),
    "Apache Kafka": ("Data Engineering", ["kafka", "apache kafka"]),
    "dbt": ("Data Engineering", ["dbt", "data build tool"]),
    "Snowflake": ("Data Engineering", ["snowflake"]),
    "BigQuery": ("Data Engineering", ["bigquery", "big query", "google bigquery"]),
    "Redshift": ("Data Engineering", ["redshift", "amazon redshift"]),
    "Databricks": ("Data Engineering", ["databricks"]),
    "Data Modelling": ("Data Engineering", ["data modelling", "data modeling", "dimensional modelling", "dimensional modeling", "star schema"]),
    "Data Warehousing": ("Data Engineering", ["data warehouse", "data warehousing", "dwh"]),
    "Hadoop": ("Data Engineering", ["hadoop", "hdfs", "hive"]),
    # Databases
    "PostgreSQL": ("Databases", ["postgresql", "postgres"]),
    "MySQL": ("Databases", ["mysql"]),
    "MongoDB": ("Databases", ["mongodb", "mongo"]),
    "SQL Server": ("Databases", ["sql server", "mssql", "ms sql"]),
    "Redis": ("Databases", ["redis"]),
    "Oracle DB": ("Databases", ["oracle database", "oracle db"]),
    # Cloud & DevOps
    "AWS": ("Cloud & DevOps", ["aws", "amazon web services", "ec2", "s3", "aws lambda", "aws glue"]),
    "Azure": ("Cloud & DevOps", ["azure", "microsoft azure", "azure data factory", "adf"]),
    "GCP": ("Cloud & DevOps", ["gcp", "google cloud", "google cloud platform"]),
    "Docker": ("Cloud & DevOps", ["docker", "containers", "containerization"]),
    "Kubernetes": ("Cloud & DevOps", ["kubernetes", "k8s"]),
    "CI/CD": ("Cloud & DevOps", ["ci/cd", "cicd", "github actions", "jenkins"]),
    "Git": ("Cloud & DevOps", ["git", "github", "gitlab", "version control"]),
    "Linux": ("Cloud & DevOps", ["linux", "unix"]),
    "Terraform": ("Cloud & DevOps", ["terraform", "infrastructure as code"]),
    # ML / DS
    "Machine Learning": ("ML & AI", ["machine learning", "ml models", "ml model", "predictive modelling", "predictive modeling"]),
    "Deep Learning": ("ML & AI", ["deep learning", "neural networks", "neural network"]),
    "Scikit-learn": ("ML & AI", ["scikit-learn", "sklearn", "scikit learn"]),
    "TensorFlow": ("ML & AI", ["tensorflow", "keras"]),
    "PyTorch": ("ML & AI", ["pytorch", "torch"]),
    "XGBoost": ("ML & AI", ["xgboost", "lightgbm", "gradient boosting"]),
    "NLP": ("ML & AI", ["nlp", "natural language processing", "text classification", "text mining"]),
    "Computer Vision": ("ML & AI", ["computer vision", "opencv", "image classification", "object detection", "yolo"]),
    "Statistics": ("ML & AI", ["statistics", "statistical analysis", "hypothesis testing", "a/b testing", "ab testing"]),
    "Feature Engineering": ("ML & AI", ["feature engineering"]),
    "Time Series": ("ML & AI", ["time series", "time-series", "forecasting", "lstm"]),
    "Recommendation Systems": ("ML & AI", ["recommendation system", "recommendation systems", "recommender", "collaborative filtering"]),
    "MLOps": ("ML & AI", ["mlops", "mlflow", "model deployment", "model monitoring", "kubeflow"]),
    "Pandas": ("ML & AI", ["pandas"]),
    "NumPy": ("ML & AI", ["numpy"]),
    # GenAI
    "LLMs": ("Generative AI", ["llm", "llms", "large language model", "large language models", "gpt", "generative ai", "genai", "gen ai"]),
    "RAG": ("Generative AI", ["rag", "retrieval augmented generation", "retrieval-augmented generation"]),
    "LangChain": ("Generative AI", ["langchain"]),
    "LangGraph": ("Generative AI", ["langgraph"]),
    "LlamaIndex": ("Generative AI", ["llamaindex", "llama index"]),
    "OpenAI API": ("Generative AI", ["openai", "openai api", "chatgpt api"]),
    "Prompt Engineering": ("Generative AI", ["prompt engineering", "prompting"]),
    "AI Agents": ("Generative AI", ["ai agents", "ai agent", "agentic", "multi-agent", "autonomous agents"]),
    "Vector Databases": ("Generative AI", ["vector database", "vector databases", "vector db", "pinecone", "chromadb", "chroma", "faiss", "weaviate", "qdrant", "pgvector"]),
    "Embeddings": ("Generative AI", ["embeddings", "embedding", "sentence transformers", "sentence-transformers", "semantic search"]),
    "Hugging Face": ("Generative AI", ["hugging face", "huggingface"]),
    "Fine-tuning": ("Generative AI", ["fine-tuning", "fine tuning", "finetuning", "lora"]),
    # Automation
    "n8n": ("Automation", ["n8n"]),
    "Zapier": ("Automation", ["zapier"]),
    "Make.com": ("Automation", ["make.com", "integromat"]),
    "Workflow Automation": ("Automation", ["workflow automation", "process automation", "business process automation", "automation workflows"]),
    "RPA": ("Automation", ["rpa", "uipath", "automation anywhere", "power automate"]),
    "REST APIs": ("Automation", ["rest api", "rest apis", "restful", "api integration", "api integrations", "apis", "webhooks", "webhook"]),
    "FastAPI": ("Automation", ["fastapi"]),
    "Flask": ("Automation", ["flask"]),
    "Selenium": ("Automation", ["selenium", "web scraping", "beautifulsoup", "playwright"]),
    "Postman": ("Automation", ["postman"]),
    # BI & analytics
    "Power BI": ("BI & Analytics", ["power bi", "powerbi", "dax", "power query"]),
    "Tableau": ("BI & Analytics", ["tableau"]),
    "Looker": ("BI & Analytics", ["looker", "looker studio", "data studio"]),
    "Excel": ("BI & Analytics", ["excel", "advanced excel", "vba", "macros", "pivot tables", "vlookup"]),
    "Data Visualization": ("BI & Analytics", ["data visualization", "data visualisation", "dashboards", "dashboard", "matplotlib", "seaborn", "plotly"]),
    "Data Analysis": ("BI & Analytics", ["data analysis", "data analytics", "data analyst", "exploratory data analysis", "eda", "analysed", "analyzed", "analysing", "analyzing"]),
    "Data Cleaning": ("BI & Analytics", ["data cleaning", "data wrangling", "data preprocessing", "data quality", "clean raw", "cleans raw", "cleaned raw", "data validation"]),
    "KPI Reporting": ("BI & Analytics", ["kpi", "kpis", "mis reporting", "business reporting", "kpi reporting"]),
    "Streamlit": ("BI & Analytics", ["streamlit"]),
    # Soft / business
    "Stakeholder Management": ("Business", ["stakeholder management", "stakeholders", "stakeholder", "cross-functional", "business teams", "presented findings"]),
    "Communication": ("Business", ["communication skills", "written and verbal communication", "presentation skills"]),
    "Agile": ("Business", ["agile", "scrum", "jira"]),
    "Problem Solving": ("Business", ["problem solving", "problem-solving", "analytical thinking"]),
}


def _compile(alias: str) -> re.Pattern:
    if alias.startswith(r"\b") or "(?" in alias or "\\" in alias:
        return re.compile(alias, re.I)
    return re.compile(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", re.I)


_PATTERNS = {skill: [_compile(a) for a in aliases] for skill, (_, aliases) in TAXONOMY.items()}


# Using a tool implies the broader skill (e.g. n8n -> Workflow Automation).
IMPLIES: dict[str, list[str]] = {
    "n8n": ["Workflow Automation"], "Zapier": ["Workflow Automation"], "Make.com": ["Workflow Automation"],
    "RPA": ["Workflow Automation"],
    "LangChain": ["LLMs"], "LangGraph": ["LLMs", "AI Agents"], "LlamaIndex": ["LLMs", "RAG"], "OpenAI API": ["LLMs"],
    "RAG": ["LLMs"], "Fine-tuning": ["LLMs"],
    "Pandas": ["Python"], "NumPy": ["Python"], "Scikit-learn": ["Python", "Machine Learning"],
    "PyTorch": ["Deep Learning"], "TensorFlow": ["Deep Learning"], "XGBoost": ["Machine Learning"],
    "Apache Spark": ["ETL"], "Apache Airflow": ["ETL"], "dbt": ["ETL", "Data Modelling"],
    "Snowflake": ["Data Warehousing"], "BigQuery": ["Data Warehousing"], "Redshift": ["Data Warehousing"],
    "PostgreSQL": ["SQL"], "MySQL": ["SQL"], "SQL Server": ["SQL"], "Power BI": ["Data Visualization"],
    "Tableau": ["Data Visualization"], "Looker": ["Data Visualization"],
}


def extract_skills(text: str, expand: bool = False) -> set[str]:
    """Return canonical skill names found in the text.

    expand=True also adds skills implied by tools (use it for resumes, not JDs).
    """
    found = {skill for skill, pats in _PATTERNS.items() if any(p.search(text) for p in pats)}
    if expand:
        for skill in list(found):
            found.update(IMPLIES.get(skill, []))
    return found


def category(skill: str) -> str:
    return TAXONOMY[skill][0]
