from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from config.basemodels import BaseContentState, ALLOWED_CONTENT_MODELS
from libs.shared_utilities import extract_text_from_url, detect_content_type, save_structured_output, print_basemodel
from libs.process_meeting_graph import process_meeting_content, create_meeting_subgraph
from libs.process_technical_article_graph import process_technical_article_content, create_technical_article_subgraph
from libs.process_news_article_graph import process_news_article_content, create_news_article_subgraph

async def node_get_content(state: BaseContentState) -> Dict[str, Any]:
    """Extract content from text or URL input."""
    if state.get("verbose", False):
        print("📥 Node: Getting content...")
        print(f"[DEBUG] processing_mode in node_get_content: {state.get('processing_mode')}")
    
    content = state.get("content", "")
    url = state.get("url", "")
    
    # If URL is provided, extract text from it
    if url and not content:
        try:
            content = await extract_text_from_url(url)
            if state.get("verbose", False):
                print(f"📄 Extracted {len(content)} characters from URL: {url}")
        except Exception as e:
            return {
                "errors": [f"Failed to extract content from URL: {str(e)}"],
                "messages": ["Content extraction failed"]
            }
    
    if not content:
        return {
            "errors": ["No content provided"],
            "messages": ["Content validation failed"]
        }
    
    return {
        "content": content,
        "messages": ["Content successfully retrieved"]
    }

async def node_content_type_detection(state: BaseContentState) -> Dict[str, Any]:
    """Detect content type and dispatch to appropriate processor."""
    if state.get("verbose", False):
        print("🔍 Node: Detecting content type...")
        print(f"[DEBUG] processing_mode in node_content_type_detection: {state.get('processing_mode')}")
    
    content = state.get("content", "")
    content_type = state.get("content_type", "auto")
    
    # If content_type is auto, detect it
    if content_type == "auto":
        detected_type, confidence = await detect_content_type(
            content=content,
            llm_provider=state.get("llm_provider"),
            model=state.get("model"),
            verbose=state.get("verbose", False)
        )
        content_type = detected_type
        
        if state.get("verbose", False):
            print(f"🎯 Detected content type: {content_type} (confidence: {confidence:.2f})")
    
    # Dispatch to appropriate processor
    if content_type == "meeting":
        try:
            if state.get("verbose", False):
                print("🔄 Invoking meeting subgraph...")
            meeting_subgraph = create_meeting_subgraph()
            subgraph_result = await meeting_subgraph.ainvoke(state)
            if subgraph_result.get("errors"):
                return {
                    "content_type": content_type,
                    "errors": subgraph_result.get("errors", []),
                    "messages": subgraph_result.get("messages", [])
                }
            return {
                "content_type": content_type,
                "summary_model": subgraph_result.get("summary_model"),
                "structured_output": subgraph_result.get("structured_output"),
                "messages": subgraph_result.get("messages", []),
                "processing_mode": subgraph_result.get("processing_mode")
            }
        except Exception as e:
            return {
                "content_type": content_type,
                "errors": [f"Error processing {content_type} content: {str(e)}"],
                "messages": ["Content processing failed"]
            }
    elif content_type == "technical_article":
        try:
            if state.get("verbose", False):
                print("🔄 Invoking technical article subgraph...")
            tech_article_subgraph = create_technical_article_subgraph()
            subgraph_result = await tech_article_subgraph.ainvoke(state)
            if subgraph_result.get("errors"):
                return {
                    "content_type": content_type,
                    "errors": subgraph_result.get("errors", []),
                    "messages": subgraph_result.get("messages", [])
                }
            return {
                "content_type": content_type,
                "summary_model": subgraph_result.get("summary_model"),
                "structured_output": subgraph_result.get("structured_output"),
                "messages": subgraph_result.get("messages", []),
                "processing_mode": subgraph_result.get("processing_mode")
            }
        except Exception as e:
            return {
                "content_type": content_type,
                "errors": [f"Error processing {content_type} content: {str(e)}"],
                "messages": ["Content processing failed"]
            }
    elif content_type == "news_article":
        try:
            if state.get("verbose", False):
                print("🔄 Invoking news article subgraph...")
            news_article_subgraph = create_news_article_subgraph()
            subgraph_result = await news_article_subgraph.ainvoke(state)
            if subgraph_result.get("errors"):
                return {
                    "content_type": content_type,
                    "errors": subgraph_result.get("errors", []),
                    "messages": subgraph_result.get("messages", [])
                }
            return {
                "content_type": content_type,
                "summary_model": subgraph_result.get("summary_model"),
                "structured_output": subgraph_result.get("structured_output"),
                "messages": subgraph_result.get("messages", []),
                "processing_mode": subgraph_result.get("processing_mode")
            }
        except Exception as e:
            return {
                "content_type": content_type,
                "errors": [f"Error processing {content_type} content: {str(e)}"],
                "messages": ["Content processing failed"]
            }
    
    # For other content types (future implementation)
    return {
        "content_type": content_type,
        "errors": [f"Content type '{content_type}' not yet implemented"],
        "messages": ["Content type not supported"]
    }

async def node_validate_content(state: BaseContentState) -> Dict[str, Any]:
    """Validate processed content."""
    if state.get("verbose", False):
        print("✅ Node: Validating content...")
        print(f"[DEBUG] processing_mode in node_validate_content: {state.get('processing_mode')}")
    
    if state.get("errors"):
        return {"messages": ["Validation skipped due to errors"]}
    
    structured_output = state.get("structured_output")
    if not structured_output:
        return {
            "errors": ["No structured output to validate"],
            "messages": ["Validation failed"]
        }
    
    return {"messages": ["Content validation passed"]}

async def node_save_content(state: BaseContentState) -> Dict[str, Any]:
    """Save structured output to file."""
    if state.get("verbose", False):
        print("💾 Node: Saving content...")
        print(f"[DEBUG] processing_mode in node_save_content: {state.get('processing_mode')}")
    
    if state.get("errors"):
        return {"messages": ["Save skipped due to errors"]}
    
    structured_output = state.get("structured_output")
    content_type = state.get("content_type", "general")
    processing_mode = state.get("processing_mode") if "processing_mode" in state else None
    
    if structured_output:
        try:
            # Add processing_mode to processing_metadata if present
            output_dict = dict(structured_output)
            if "processing_metadata" in output_dict and isinstance(output_dict["processing_metadata"], dict):
                output_dict["processing_metadata"]["processing_mode"] = processing_mode
            filename = save_structured_output(output_dict, content_type, processing_mode=processing_mode)
            return {
                "messages": [f"Content saved to {filename}"],
                "output_file": filename
            }
        except Exception as e:
            return {
                "errors": [f"Failed to save content: {str(e)}"],
                "messages": ["Save failed"]
            }
    
    return {"messages": ["No content to save"]}

async def node_return_response(state: BaseContentState) -> Dict[str, Any]:
    """Format and return final response."""
    if state.get("verbose", False):
        print("📤 Node: Returning response...")
        print(f"[DEBUG] processing_mode in node_return_response: {state.get('processing_mode')}")
    
    summary_model = state.get("summary_model")
    
    if summary_model and state.get("verbose", False):
        print_basemodel(summary_model, f"Final {state.get('content_type', 'Content')} Summary")
    
    final_output = {
        "success": len(state.get("errors", [])) == 0,
        "content_type": state.get("content_type", "unknown"),
        "structured_output": state.get("structured_output"),
        "output_file": state.get("output_file"),
        "messages": state.get("messages", []),
        "errors": state.get("errors", [])
    }
    
    return {"final_output": final_output}

def create_graph() -> StateGraph:
    """Create the main processing graph with linear flow."""
    # Create graph with BaseContentState
    graph = StateGraph(BaseContentState)
    
    # Add nodes in linear order
    graph.add_node("get_content", node_get_content)
    graph.add_node("content_type_detection", node_content_type_detection)
    graph.add_node("validate_content", node_validate_content)
    graph.add_node("save_content", node_save_content)
    graph.add_node("return_response", node_return_response)
    
    # Define linear flow
    graph.add_edge("get_content", "content_type_detection")
    graph.add_edge("content_type_detection", "validate_content")
    graph.add_edge("validate_content", "save_content")
    graph.add_edge("save_content", "return_response")
    graph.add_edge("return_response", END)
    
    # Set entry point
    graph.set_entry_point("get_content")
    
    return graph.compile()

# Main function to process content using the graph
async def process_content_with_graph(
    content: str = "",
    url: str = "",
    content_type: str = "auto",
    llm_provider: Optional[str] = None,
    model: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """Process content using the graph factory."""
    import os
    processing_mode = os.getenv("PROCESSING_MODE", "single")
    # Create initial state
    initial_state = BaseContentState(
        content=content,
        content_type=content_type,
        url=url,
        llm_provider=llm_provider,  # Let initialize_llm handle defaults
        model=model,  # Let initialize_llm handle defaults
        verbose=verbose,
        extra_args={},
        messages=[],
        errors=[],
        summary_model=None,
        structured_output={},
        final_output={},
        processing_mode=processing_mode
    )
    # Create and run graph
    graph = create_graph()
    result = await graph.ainvoke(initial_state)
    return result.get("final_output", {}) 