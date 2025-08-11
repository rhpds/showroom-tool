#!/usr/bin/env python

"""
LangGraph factory for processing Showroom repositories.

This module provides a LangGraph-based approach to fetching and processing
Showroom repositories with proper state management and error handling.
"""

from typing import Any, Literal, cast

from langgraph.graph import END, StateGraph

from config.basemodels import (
    CatalogDescription,
    ShowroomReview,
    ShowroomState,
    ShowroomSummary,
)
from showroom_tool.showroom import fetch_showroom_repository
from showroom_tool.shared_utilities import (
    build_showroom_description_prompt,
    build_showroom_review_prompt,
    build_showroom_summary_prompt,
    process_content_with_structured_output,
)


async def get_showroom(state: ShowroomState) -> dict[str, Any]:
    """
    LangGraph node to fetch showroom repository data.

    This node encapsulates the existing showroom fetching logic
    and returns the processed Showroom data.
    """
    if state.verbose:
        print("🏢 Node: Getting showroom repository data...")

    try:
        # Use the existing fetch_showroom_repository function
        showroom = fetch_showroom_repository(
            git_url=state.git_url,
            git_ref=state.git_ref,
            verbose=state.verbose,
            cache_dir=state.cache_dir,
            no_cache=state.no_cache,
            local_dir=state.local_dir,
        )

        if showroom is None:
            return {
                "errors": [f"Failed to fetch showroom repository from {state.git_url}"],
                "messages": ["Showroom fetch failed"]
            }

        if state.verbose:
            print(f"✅ Successfully fetched showroom: '{showroom.lab_name}' with {len(showroom.modules)} modules")

        # If no command provided, prepare final_output here so callers that only fetch get a response
        base = {
            "showroom": showroom,
            "messages": [
                f"Successfully fetched showroom: '{showroom.lab_name}' with {len(showroom.modules)} modules"
            ],
        }
        if state.command is None:
            base["final_output"] = {
                "success": True,
                "lab_name": showroom.lab_name,
                "git_url": showroom.git_url,
                "git_ref": showroom.git_ref,
                "module_count": len(showroom.modules),
                "showroom_data": showroom,
            }
        return base

    except Exception as e:
        error_msg = f"Unexpected error fetching showroom: {str(e)}"
        return {
            "errors": [error_msg],
            "messages": ["Showroom processing failed"],
            "final_output": {
                "success": False,
                "error": error_msg
            }
        }

async def process_showroom(state: ShowroomState) -> dict[str, Any]:
    """Process showroom data according to the verb in state.command.

    Supported commands: summary, review, description
    """
    if state.verbose:
        print("🧠 Node: Processing showroom with LLM...")

    showroom = state.showroom
    if showroom is None:
        return {
            "errors": ["No showroom data available to process"],
            "messages": ["Processing skipped due to missing showroom"],
        }

    command = state.command or "summary"

    try:
        if command == "summary":
            system_prompt, user_content = build_showroom_summary_prompt(showroom, ShowroomSummary)
            model_class = ShowroomSummary
        elif command == "review":
            system_prompt, user_content = build_showroom_review_prompt(showroom, ShowroomReview)
            model_class = ShowroomReview
        elif command == "description":
            system_prompt, user_content = build_showroom_description_prompt(showroom, CatalogDescription)
            model_class = CatalogDescription
        else:
            return {
                "errors": [f"Unknown command: {command}"],
                "messages": ["Unsupported processing command"],
            }

        result, success, metadata = await process_content_with_structured_output(
            content=user_content,
            model_class=model_class,
            system_prompt=system_prompt,
            llm_provider=state.llm_provider,
            model=state.model,
            temperature=state.temperature,
            verbose=state.verbose,
        )

        if not success or result is None:
            return {
                "errors": [metadata.get("error", "Failed to generate structured output")],
                "messages": ["LLM processing failed"],
                "final_output": {
                    "success": False,
                    "error": metadata.get("error", "Failed to generate structured output"),
                },
            }

        # Attach result to showroom for downstream usage
        if command == "summary":
            showroom.summary_output = cast(ShowroomSummary, result)
        elif command == "review":
            showroom.review_output = cast(ShowroomReview, result)
        elif command == "description":
            showroom.description_output = cast(CatalogDescription, result)

        final_output: dict[str, Any] = {
            "success": True,
            "lab_name": showroom.lab_name,
            "git_url": showroom.git_url,
            "git_ref": showroom.git_ref,
            "module_count": len(showroom.modules),
            "showroom_data": showroom,
            "structured_output": result.model_dump() if hasattr(result, "model_dump") else result,
            "command": command,
        }

        return {"final_output": final_output}

    except Exception as e:
        error_msg = f"Unexpected error processing showroom: {str(e)}"
        return {
            "errors": [error_msg],
            "messages": ["Showroom processing failed"],
            "final_output": {"success": False, "error": error_msg},
        }


def graph_factory(include_processing: bool = True):
    """
    Create a linear LangGraph with START -> get_showroom -> process_showroom -> END.

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(ShowroomState)
    graph.add_node("get_showroom", get_showroom)
    if include_processing:
        graph.add_node("process_showroom", process_showroom)
        graph.add_edge("get_showroom", "process_showroom")
        graph.add_edge("process_showroom", END)
    else:
        graph.add_edge("get_showroom", END)
    graph.set_entry_point("get_showroom")
    return graph.compile()


async def process_showroom_with_graph(
    git_url: str,
    git_ref: str = "main",
    verbose: bool = False,
    cache_dir: str | None = None,
    no_cache: bool = False,
    local_dir: str | None = None,
    command: Literal["summary", "review", "description"] | None = None,
    llm_provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> dict[str, Any]:
    """
    Process a showroom repository using the LangGraph approach.

    Args:
        git_url: URL of the git repository
        git_ref: Git reference to checkout (branch, tag, or commit)
        verbose: Enable verbose output
        cache_dir: Custom cache directory (uses default if None)
        no_cache: Disable caching and force fresh clone

    Returns:
        Dictionary containing processing results and showroom data
    """
    # Create initial state
    initial_state = ShowroomState(
        git_url=git_url,
        git_ref=git_ref,
        verbose=verbose,
        cache_dir=cache_dir,
        no_cache=no_cache,
        local_dir=local_dir,
        command=command,
        llm_provider=llm_provider,
        model=model,
        temperature=temperature,
        messages=[],
        errors=[],
        final_output={},
    )

    # Create and run graph
    graph = graph_factory(include_processing=command is not None)
    result = await graph.ainvoke(initial_state)
    # If process_showroom succeeded, final_output will be present; otherwise fallback
    return result.get("final_output", {})
