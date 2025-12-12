import streamlit as st
import pandas as pd
import numpy as np
import datetime

def render():
    """
    Render the API Management page.
    Displays Usage & Billing chart and Model Configuration table.
    """
    st.markdown('<div class="hero-title">API Management</div>', unsafe_allow_html=True)
    st.caption("Manage and view the AI models powering Studio IPX services.")
    
    # --- 1. Usage & Billing ---
    st.markdown("""
    <div class="notion-card">
        <div class="section-header">💲 Usage & Billing</div>
        <div style="color: #8B949E; font-size: 0.9rem;">Real-time cost tracking</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mock Data for Chart
    dates = pd.date_range(start="2025-12-01", end="2025-12-12")
    usage_data = pd.DataFrame({
        "Date": dates,
        "Gemini Developer API": np.random.uniform(100, 500, len(dates)),
        "Firebase Services": np.random.uniform(50, 200, len(dates)),
        "Cloud Storage": np.random.uniform(10, 50, len(dates))
    })
    usage_data = usage_data.set_index("Date")
    
    st.area_chart(usage_data, color=["#2383E2", "#FF6B6B", "#FFD93D"])
    
    # Service Breakdown
    col1, col2, col3 = st.columns(3)
    col1.metric("Gemini Developer API", "₩4,250", "+12%")
    col2.metric("Firebase Services", "₩1,200", "+5%")
    col3.metric("Cloud Storage", "₩350", "+2%")
    
    st.markdown("---")
    
    # --- 2. Model Configuration ---
    st.markdown("""
    <div class="notion-card">
        <div class="section-header">⚙️ Model Configuration</div>
        <div style="color: #8B949E; font-size: 0.9rem;">
            Caution: Changing models may affect output quality.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mock Data for Table
    model_config = pd.DataFrame([
        {
            "Feature": "Image Generation (Standard)",
            "Service Name": "Nano Banana",
            "Model ID": "gemini-2.0-flash-image",
            "Status": "ACTIVE",
            "Description": "High-speed image generation model optimized for rapid iteration."
        },
        {
            "Feature": "Image Generation (Pro)",
            "Service Name": "Nano Banana Pro",
            "Model ID": "gemini-1.5-pro-image-preview",
            "Status": "ACTIVE",
            "Description": "High-fidelity model for professional commercial photography."
        },
        {
            "Feature": "Chat Assistant",
            "Service Name": "Studio Assistant",
            "Model ID": "gemini-2.0-flash",
            "Status": "ACTIVE",
            "Description": "RAG-enabled chatbot capable of answering questions based on Knowledge Base."
        }
    ])
    
    # Data Editor for "Model ID" simulation
    edited_df = st.data_editor(
        model_config,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                help="The status of the model",
                width="small",
                options=["ACTIVE", "MAINTENANCE", "DEPRECATED"],
                required=True,
            ),
            "Model ID": st.column_config.SelectboxColumn(
                "Model ID",
                help="Select the AI model",
                width="medium",
                options=[
                    "gemini-2.0-flash-image",
                    "gemini-1.5-pro-image-preview",
                    "gemini-2.0-flash",
                    "gemini-1.5-flash",
                    "gemini-1.5-pro"
                ],
                required=True,
            )
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed"
    )
    
    if st.button("💾 Save Configuration"):
        st.success("Configuration saved successfully!")
        st.balloons()
