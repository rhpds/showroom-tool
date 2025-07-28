#!/usr/bin/env python

"""
LangGraph factory for processing Showroom repositories.

This module provides a LangGraph-based approach to fetching and processing
Showroom repositories with proper state management and error handling.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from config.basemodels import ShowroomState
from showroom_tool.showroom import fetch_showroom_repository


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
            no_cache=state.no_cache
        )

        if showroom is None:
            return {
                "errors": [f"Failed to fetch showroom repository from {state.git_url}"],
                "messages": ["Showroom fetch failed"]
            }

        if state.verbose:
            print(f"✅ Successfully fetched showroom: '{showroom.lab_name}' with {len(showroom.modules)} modules")

        return {
            "showroom": showroom,
            "messages": [f"Successfully fetched showroom: '{showroom.lab_name}' with {len(showroom.modules)} modules"],
            "final_output": {
                "success": True,
                "lab_name": showroom.lab_name,
                "git_url": showroom.git_url,
                "git_ref": showroom.git_ref,
                "module_count": len(showroom.modules),
                "showroom_data": showroom
            }
        }

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


def graph_factory():
    """
    Create a simple LangGraph with START -> get_showroom -> END flow.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with ShowroomState
    graph = StateGraph(ShowroomState)

    # Add the single node
    graph.add_node("get_showroom", get_showroom)

    # Define simple linear flow: START -> get_showroom -> END
    graph.add_edge("get_showroom", END)

    # Set entry point
    graph.set_entry_point("get_showroom")

    return graph.compile()


async def process_showroom_with_graph(
    git_url: str,
    git_ref: str = "main",
    verbose: bool = False,
    cache_dir: str | None = None,
    no_cache: bool = False
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
        messages=[],
        errors=[],
        final_output={}
    )

    # Create and run graph
    graph = graph_factory()
    result = await graph.ainvoke(initial_state)

    return result.get("final_output", {})
