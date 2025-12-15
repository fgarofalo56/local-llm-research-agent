"""
Documents Page - Streamlit Multi-Page App
Phase 2.1+ Document Management UI

Features:
- Document list with processing status
- File upload with drag-and-drop
- Document deletion
- Status indicators (pending, processing, completed, failed)
- Reprocess failed documents
"""

import asyncio
import contextlib
from datetime import datetime

import httpx
import streamlit as st

from src.utils.config import settings

# Page configuration
st.set_page_config(
    page_title="Documents - Local LLM Research Agent",
    page_icon="📄",
    layout="wide",
)

# API base URL - use environment variable or default to localhost
API_BASE_URL = f"http://localhost:{settings.api_port}"


def run_async(coro):
    """Run async code in Streamlit's sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def fetch_documents(skip: int = 0, limit: int = 20) -> dict:
    """Fetch documents from API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/api/documents",
                params={"skip": skip, "limit": limit},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"documents": [], "total": 0, "error": str(e)}


async def upload_document(file_content: bytes, filename: str) -> dict:
    """Upload a document to API."""
    async with httpx.AsyncClient() as client:
        try:
            files = {"file": (filename, file_content)}
            response = await client.post(
                f"{API_BASE_URL}/api/documents",
                files=files,
                timeout=60.0,
            )
            response.raise_for_status()
            return {"success": True, "document": response.json()}
        except httpx.HTTPError as e:
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                with contextlib.suppress(Exception):
                    error_detail = e.response.json().get("detail", str(e))
            return {"success": False, "error": error_detail}


async def delete_document(document_id: int) -> dict:
    """Delete a document via API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{API_BASE_URL}/api/documents/{document_id}",
                timeout=10.0,
            )
            response.raise_for_status()
            return {"success": True}
        except httpx.HTTPError as e:
            return {"success": False, "error": str(e)}


async def reprocess_document(document_id: int) -> dict:
    """Reprocess a failed document via API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/documents/{document_id}/reprocess",
                timeout=10.0,
            )
            response.raise_for_status()
            return {"success": True}
        except httpx.HTTPError as e:
            # Endpoint may not exist yet
            return {"success": False, "error": str(e)}


def get_status_badge(status: str) -> str:
    """Get status badge for document processing status."""
    badges = {
        "pending": "🟡 Pending",
        "processing": "🔵 Processing",
        "completed": "🟢 Completed",
        "failed": "🔴 Failed",
    }
    return badges.get(status, f"⚪ {status}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_datetime(dt_str: str | None) -> str:
    """Format datetime string for display."""
    if not dt_str:
        return "-"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        # Return original string if datetime parsing fails
        return dt_str


def render_document_list():
    """Render the document list."""
    st.subheader("Uploaded Documents")

    # Fetch documents
    with st.spinner("Loading documents..."):
        result = run_async(fetch_documents(limit=50))

    if "error" in result:
        st.error(f"Failed to load documents: {result['error']}")
        st.info("Make sure the API server is running at " + API_BASE_URL)
        return

    documents = result.get("documents", [])
    total = result.get("total", 0)

    if not documents:
        st.info("No documents uploaded yet. Use the upload section above to add documents.")
        return

    st.caption(f"Total: {total} documents")

    # Create a table-like display
    for doc in documents:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 2, 1])

        with col1:
            st.markdown(f"**{doc['original_filename']}**")
            st.caption(format_file_size(doc["file_size"]))

        with col2:
            st.markdown(get_status_badge(doc["processing_status"]))
            if doc["processing_status"] == "failed" and doc.get("error_message"):
                st.caption(f"Error: {doc['error_message'][:50]}...")

        with col3:
            if doc.get("chunk_count"):
                st.metric("Chunks", doc["chunk_count"])
            else:
                st.caption("-")

        with col4:
            st.caption(f"Uploaded: {format_datetime(doc['created_at'])}")
            if doc.get("processed_at"):
                st.caption(f"Processed: {format_datetime(doc['processed_at'])}")

        with col5:
            # Action buttons
            if doc["processing_status"] == "failed" and st.button(
                "🔄", key=f"reprocess_{doc['id']}", help="Reprocess"
            ):
                result = run_async(reprocess_document(doc["id"]))
                if result["success"]:
                    st.toast("Reprocessing started", icon="🔄")
                    st.rerun()
                else:
                    st.error(f"Failed: {result.get('error', 'Unknown error')}")

            if st.button("🗑️", key=f"delete_{doc['id']}", help="Delete"):
                # Use session state for confirmation
                st.session_state[f"confirm_delete_{doc['id']}"] = True

        # Confirmation dialog
        if st.session_state.get(f"confirm_delete_{doc['id']}"):
            st.warning(f"Are you sure you want to delete '{doc['original_filename']}'?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, delete", key=f"confirm_yes_{doc['id']}", type="primary"):
                    result = run_async(delete_document(doc["id"]))
                    if result["success"]:
                        st.toast("Document deleted", icon="✅")
                        del st.session_state[f"confirm_delete_{doc['id']}"]
                        st.rerun()
                    else:
                        st.error(f"Failed to delete: {result.get('error', 'Unknown error')}")
            with col_no:
                if st.button("Cancel", key=f"confirm_no_{doc['id']}"):
                    del st.session_state[f"confirm_delete_{doc['id']}"]
                    st.rerun()

        st.divider()


def render_upload_section():
    """Render the document upload section."""
    st.subheader("Upload Documents")

    # Supported file types
    supported_types = [".pdf", ".docx", ".pptx", ".xlsx", ".html", ".md", ".txt"]
    st.caption(f"Supported formats: {', '.join(supported_types)}")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=[t.lstrip(".") for t in supported_types],
        help="Select a document to upload for RAG processing",
        key="document_uploader",
    )

    if uploaded_file is not None:
        # Show file info
        st.info(f"Selected: **{uploaded_file.name}** ({format_file_size(uploaded_file.size)})")

        # Upload button
        if st.button("Upload Document", type="primary", use_container_width=True):
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                content = uploaded_file.read()
                result = run_async(upload_document(content, uploaded_file.name))

            if result["success"]:
                st.success("Document uploaded successfully! Processing started.")
                st.balloons()
                # Clear the uploader by rerunning
                st.rerun()
            else:
                st.error(f"Upload failed: {result.get('error', 'Unknown error')}")


def main():
    """Main page entry point."""
    st.title("📄 Document Management")
    st.caption("Upload and manage documents for RAG (Retrieval-Augmented Generation)")

    # Upload section first
    render_upload_section()

    st.divider()

    # Document list with refresh button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    render_document_list()


if __name__ == "__main__":
    main()
