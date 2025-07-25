from typing import List, Optional, Literal, Dict, Any, TypedDict, Union
from pydantic import BaseModel, Field
from datetime import datetime
import operator
from typing_extensions import Annotated

# =============================================
# Dynamic Content Type Registry
# =============================================

# Strict processing metadata model for OpenAI structured outputs
class ProcessingMetadata(BaseModel):
    timestamp: str = Field(..., description="ISO timestamp of processing")
    llm_provider: str = Field(..., description="LLM provider used")
    model_name: str = Field(..., description="Model name used")
    processing_duration: Optional[float] = Field(None, description="Processing duration in seconds")
    success: bool = Field(..., description="Whether processing was successful")
    note: Optional[str] = Field(None, description="Optional note")
    
    model_config = {"extra": "forbid"}  # This sets additionalProperties: false

# Forward declarations needed for the registry
class BaseContentSummary(BaseModel):
    """Base class for all content summaries with common fields."""
    content_type: str = Field(
        ...,
        description="Type of content (meeting, news, tutorial, general)",
        avoid_processing=True
    )
    processing_metadata: ProcessingMetadata = Field(
        ...,
        description="Processing metadata including: timestamp, llm_provider, model_name, model_version, processing_duration, etc.",
        avoid_processing=True
    )

class MeetingSummary(BaseContentSummary):
    """Structure for desired output of meeting summary."""
    content_type: Literal["meeting"] = Field(
        default="meeting",
        description="Must be exactly 'meeting' for meeting summaries"
    )
    
    overview: str = Field(
        ...,
        min_length=10,
        description="FOCUS: High-level meeting purpose and key outcomes only. IGNORE: Specific tasks, individual names, detailed discussions. ACT LIKE: Executive getting a 30-second briefing. WRITE: 1-3 sentences about what this meeting accomplished and why it mattered."
    )
    
    topics_discussed: List[str] = Field(
        default_factory=list,
        description="FOCUS: Major discussion themes and subject areas only. IGNORE: Specific decisions, tasks, or personal details. ACT LIKE: Someone cataloging conversation topics. WRITE: 2-3 full sentences describing what subjects were covered. Group related subtopics together."
    )
    
    participants: List[str] = Field(
        default_factory=list,
        description="Extract participant names as mentioned in the transcript. If only a first name is mentioned, and a matching full name is provided in the context hints in the system prompt, use the full name from the context hints. Do not invent names not present in the transcript or context hints."
    )
    
    decisions_made: List[str] = Field(
        default_factory=list,
        description="FOCUS: Concrete choices and resolutions only. IGNORE: Discussions, suggestions, or maybes. ACT LIKE: Board secretary recording official decisions. WRITE: Clear, complete sentences stating what was definitively decided or agreed upon."
    )
    
    action_items: List[str] = Field(
        default_factory=list,
        description="FOCUS: WHO is doing WHAT by WHEN. IGNORE: General discussions or decisions. ACT LIKE: Project manager tracking assignments. WRITE: Complete sentences that clearly state the person, the specific task, and any deadlines mentioned."
    )
    
    disagreements: List[str] = Field(
        default_factory=list,
        description="FOCUS: Conflicts, debates, and opposing viewpoints only. IGNORE: Friendly discussions or agreements. ACT LIKE: Mediator noting points of contention. WRITE: Full sentences describing what people disagreed about and any resolutions reached."
    )
    
    personal_notes: List[str] = Field(
        default_factory=list,
        description="FOCUS: Human moments, hobbies, personal sharing, and informal comments. IGNORE: Work tasks and business discussions. ACT LIKE: Someone getting to know colleagues personally. WRITE: Personal details, jokes, life updates, or casual mentions people shared."
    )
    
    deadlines: List[str] = Field(
        default_factory=list,
        description="FOCUS: Specific dates, times, and timeframes only. IGNORE: Vague timing like 'soon' or 'later'. ACT LIKE: Calendar scheduler. WRITE: Exact dates, times, and deadlines mentioned with clear context about what needs to happen by when."
    )

class TechnicalArticleSummary(BaseContentSummary):
    """
    Structured summary of a technical article for both sales and technical AI professionals.
    Inspired by the MeetingSummary format for clarity and utility.
    """
    content_type: Literal["technical_article"] = Field(
        default="technical_article",
        description="Must be exactly 'technical_article' for technical article summaries"
    )
    title: str = Field(..., description="The title of the article, as published.")
    overview: str = Field(
        ..., 
        min_length=10,
        description="1-3 sentences summarizing the entire article. FOCUS: The topic, goal, and main takeaway. IGNORE: Small details or formatting. ACT LIKE: A high-level editor summarizing why this article matters."
    )
    top_takeaways: List[str] = Field(
        ...,  # required
        min_items=1,
        description="Focusing on 3–5 of the most important insights, conclusions, or key points presented in the article. WRITE: Clear, complete thoughts that can stand alone."
    )
    # for_ai_sales: List[str] = Field(
    #     default_factory=list,
    #     description="What an AI-focused sales professional should know. FOCUS: Business value, customer pain points, positioning, use cases. ACT LIKE: A solution engineer giving talking points."
    # )
    # for_ai_architects: List[str] = Field(
    #     default_factory=list,
    #     description="What a technical AI architect or engineer should know. FOCUS: Architecture patterns, model details, stack choices, constraints, integration points."
    # )
    source_url: Optional[str] = Field(None, description="Link to the original article. DONT MAKE IT UP IF YOU CAN'T FIND IT.")
    publication_date: Optional[str] = Field(None, description="Date the article was published, if known. DONT MAKE IT UP IF YOU CAN'T FIND IT.")
    publisher: Optional[str] = Field(None, description="Name of the publisher or platform. DONT MAKE IT UP IF YOU CAN'T FIND IT.")
    technologies_mentioned: List[str] = Field(
        default_factory=list,
        description="List specific frameworks, models, protocols, tools, or services referenced. e.g., LangChain, LlamaIndex, Hugging Face, OpenAI, vLLM, Triton, etc."
    )
    code_snippets: List[str] = Field(
        default_factory=list,
        description="All code snippets found in the article. SAVE THE CODE SNIPPETS IN A CODE BLOCK."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Topical tags or keywords relevant to the content. e.g., RAG, LLMOps, Prompt Engineering."
    )
    reading_time_minutes: Optional[int] = Field(
        None, 
        description="Estimated reading time in minutes. Based on average reading speed or stated by the article."
    )
    llm_ready_metadata: Optional[str] = Field(
        None,
        description="Optional YAML or markdown block summarizing this object for use in LLM ingestion or knowledge base."
    )

class NewsArticleSummary(BaseContentSummary):
    """Structure for desired output of news article summary."""
    content_type: Literal["news_article"] = Field(
        default="news_article",
        description="Must be exactly 'news_article' for news article summaries"
    )
    
    title: str = Field(..., description="The headline/title of the news article")
    
    overview: str = Field(
        ...,
        min_length=10,
        description="FOCUS: Main story and key facts only. IGNORE: Editorial opinions, minor details. ACT LIKE: Wire service editor. WRITE: 2-3 sentences summarizing who, what, when, where, why, and how."
    )
    
    key_claims: List[str] = Field(
        default_factory=list,
        description="FOCUS: Concrete statements, statistics, quotes, and claims made in the article. IGNORE: Opinions or speculation. ACT LIKE: News analyst. WRITE: Clear, complete sentences capturing what the article claims, not verifying if it's true."
    )
    
    political_entities: List[str] = Field(
        default_factory=list,
        description="Extract names of politicians, political parties, government agencies, and political organizations mentioned in the article. Include both domestic and international entities. Include full names and titles when available. ONLY EXTRACT WHAT IS EXPLICITLY MENTIONED IN THE ARTICLE."
    )
    
    policy_implications: List[str] = Field(
        default_factory=list,
        description="FOCUS: Policy impacts, legislative effects, or governance consequences explicitly stated in the article. IGNORE: Personal opinions, partisan commentary, or your own analysis. ACT LIKE: Policy analyst. WRITE: Only what is directly mentioned about policy implications. DO NOT MAKE YOUR OWN IMPLICATIONS."
    )
    
    timeline_events: List[str] = Field(
        default_factory=list,
        description="FOCUS: Chronological sequence of events, dates, and timeframes mentioned in the article only. IGNORE: Future predictions, hypothetical scenarios, or any information not explicitly stated. ACT LIKE: Timeline curator. WRITE: Clear chronological order with specific dates when available. DO NOT MAKE UP OR INFER DATES."
    )
    
    stakeholders_affected: List[str] = Field(
        default_factory=list,
        description="FOCUS: Groups, organizations, or populations directly impacted by the news. IGNORE: General public or vague references. ACT LIKE: Impact analyst. WRITE: Specific groups with clear connection to the story."
    )
    
    source_url: Optional[str] = Field(None, description="Link to the original article. DONT MAKE IT UP IF YOU CAN'T FIND IT.")
    publication_date: Optional[str] = Field(None, description="Date the article was published, if known. DONT MAKE IT UP IF YOU CAN'T FIND IT.")
    publisher: Optional[str] = Field(None, description="Name of the publisher or platform. DONT MAKE IT UP IF YOU CAN'T FIND IT.")
    author: Optional[str] = Field(None, description="Author of the article, if mentioned. DONT MAKE IT UP IF YOU CAN'T FIND IT.")
    
    tags: List[str] = Field(
        default_factory=list,
        description="Topical tags relevant to the content. Let the LLM generate appropriate tags based on the article content. e.g., 'Elections', 'Foreign Policy', 'Domestic Politics', 'Economy'."
    )
    
    reading_time_minutes: Optional[int] = Field(
        None, 
        description="Estimated reading time in minutes. Calculate based on word count using average reading speed (200-250 words per minute)."
    )

# =============================================
# CONTENT TYPE REGISTRY - ADD NEW TYPES HERE
# =============================================

ALLOWED_CONTENT_MODELS = {
    "meeting": MeetingSummary,
    "technical_article": TechnicalArticleSummary,
    "news_article": NewsArticleSummary,
    # Add new content types here:
    # "tutorial": TutorialSummary,
}

# =============================================
# LangGraph State Management
# =============================================

class ContextHint(BaseModel):
    """A single context hint with label and data"""
    hint_label: str = Field(..., description="Human-readable label for this hint type")
    hint_data: Union[List[str], List[Dict[str, str]], Dict[str, str], str] = Field(
        ..., 
        description="The actual context data - can be list, dict, or string"
    )
    confidence: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0,
        description="Confidence in this hint's accuracy"
    )
    source: str = Field(
        default="agent",
        description="Source of this hint (calendar, glossary, agent, etc.)"
    )

class ContextHints(BaseModel):
    """Collection of context hints from various sources"""
    content_type: str = Field(..., description="Content type these hints apply to")
    hints: List[ContextHint] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the context collection"
    )

# Update BaseContentState to include context_hints
class BaseContentState(TypedDict):
    """
    Unified state schema for all content types in LangGraph workflows.
    Compatible with LangGraph StateGraph and supports type-specific model instances.
    """
    # Input data
    content: str
    content_type: str  # "meeting", "news", "tutorial", "auto"
    url: Optional[str]
    
    # Configuration
    llm_provider: str
    model: str
    verbose: bool
    extra_args: Dict[str, Any]
    processing_mode: str  # <-- Add this line
    
    # Processing state
    messages: Annotated[List[str], operator.add]  # Append-only for parallel processing
    errors: Annotated[List[str], operator.add]    # Append-only for error accumulation
    
    # Output data
    summary_model: Optional[BaseModel]  # Will be populated with MeetingSummary, NewsSummary, etc.
    structured_output: Dict[str, Any]
    final_output: Dict[str, Any]
    context_hints: Optional[ContextHints]  # New field

# =============================================
# Content Type Detection
# =============================================

class ContentTypeDetection(BaseModel):
    """
    Model for auto-detecting content type using structured LLM output.
    Dynamically uses available content types from ALLOWED_CONTENT_MODELS registry.
    """
    content_type: str = Field(
        ...,
        description="Detected content type. Must be one of the available content types or 'general'"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0 for the detection"
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this content type was selected"
    )


# =============================================
# Future Content Type Models (Placeholders)
# =============================================

# class NewsSummary(BaseContentSummary):
#     """News article summary model - placeholder for future implementation."""
#     pass

# class TutorialSummary(BaseContentSummary):
#     """Tutorial summary model - placeholder for future implementation."""
#     pass
