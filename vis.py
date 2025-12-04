import streamlit as st
import pandas as pd
import io

# Page Configuration
st.set_page_config(
    page_title="Survey Response Explorer",
    page_icon="📊",
    layout="wide"
)

# Initialize Session State for row selection if it doesn't exist
if 'selected_index' not in st.session_state:
    st.session_state.selected_index = 0

def main():
    st.title("📊 Survey Response Explorer")
    st.markdown("""
    Upload your CSV file to analyze responses. 
    **Tip:** Click on any row in the table below to instantly view that person's full details.
    """)

    # --- Sidebar: File Upload ---
    st.sidebar.header("1. Data Source")
    uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

    # --- Sidebar: Sample Data Generator ---
    if uploaded_file is None:
        st.info("👋 Please upload a CSV file in the sidebar to get started.")
        
        st.markdown("---")
        st.subheader("Don't have a file handy?")
        if st.button("Load Example Survey Data"):
            data = """Response ID,Name,Satisfaction Score (1-10),What did you like most?,What can we improve?
            1,Alice Johnson,8,"The variety of options was great. I really enjoyed the user interface.","The loading speed could be a bit faster on mobile devices."
            2,Bob Smith,5,"It was okay. Nothing special standing out.","Customer support took 3 days to reply. That is unacceptable."
            3,Charlie Brown,10,"Absolutely everything! The service was impeccable and the team was friendly.","Nothing, keep doing what you are doing!"
            4,Diana Prince,3,"Not much to be honest. I found it confusing.","Make the documentation clearer. I had to guess how to use half the features."
            5,Evan Wright,9,"Very robust platform. Handles large datasets well.","Maybe add a dark mode?"
            """
            uploaded_file = io.StringIO(data)
        else:
            return

    # --- Data Loading ---
    try:
        if isinstance(uploaded_file, io.StringIO):
            df = pd.read_csv(uploaded_file)
        else:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        return

    # Add a virtual index column for reference if one doesn't exist
    if "Row_ID" not in df.columns:
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'Row_ID'}, inplace=True)

    # --- Sidebar: Configuration ---
    st.sidebar.header("2. Configuration")
    
    # Allow user to select which column acts as the "Name"
    possible_names = [col for col in df.columns if "name" in col.lower()]
    default_name_index = df.columns.get_loc(possible_names[0]) if possible_names else 0
    
    name_col = st.sidebar.selectbox(
        "Select Name/Identifier Column:",
        options=df.columns,
        index=default_name_index,
        help="This column will be used to label the individual view."
    )

    # --- Logic: Handle Selection from Overview ---
    # Check if a row was selected in the dataframe (using the key 'response_grid')
    # We must do this BEFORE the navigation widget is rendered to avoid "modifying state after instantiation" error.
    if "response_grid" in st.session_state:
        selection = st.session_state.response_grid.get("selection", {})
        if selection.get("rows"):
            st.session_state.selected_index = selection["rows"][0]
            st.session_state.view_mode_selector = "Individual Detail View"

    # --- Sidebar: Navigation ---
    st.sidebar.header("3. View Mode")
    
    view_mode = st.sidebar.radio(
        "Select View:", 
        ["Overview & Sorting", "Individual Detail View", "Question Analysis View"], 
        key="view_mode_selector"
    )

    # --- Logic: Overview Mode ---
    if view_mode == "Overview & Sorting":
        st.header("Global Overview")
        
        # REMOVED: Key Metrics Section
        
        # The Dataframe with Selection
        st.subheader("Response Data Grid")
        st.caption("Select a row below to jump to their details.")
        
        # Enable selection
        event = st.dataframe(
            df, 
            use_container_width=True, 
            height=600,                  # Increased height since metrics are gone
            on_select="rerun",           
            selection_mode="single-row",
            key="response_grid"
        )

    # --- Logic: Detail Mode ---
    elif view_mode == "Individual Detail View":
        st.header("Individual Response Viewer")
        
        # Sidebar Selection for this mode
        st.sidebar.markdown("---")
        st.sidebar.subheader("Select Respondent")
        
        def get_label(index):
            val = df.iloc[index][name_col]
            return f"{val} (Row {index})"

        selected_index = st.sidebar.selectbox(
            "Viewing Record:",
            options=df.index,
            index=st.session_state.selected_index, 
            format_func=get_label
        )
        
        st.session_state.selected_index = selected_index
        row_data = df.iloc[selected_index]

        # Header
        st.markdown(f"### 👤 {row_data[name_col]}")
        st.divider()

        # REMOVED: Quick Facts Header Section

        # B. Detailed Responses (Now containing everything)
        
        # CSS for the custom boxes
        st.markdown("""
        <style>
        .response-box {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            border-left: 6px solid #4e8cff;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .response-question {
            font-weight: bold;
            color: #31333F;
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        .response-answer {
            color: #1f1f1f;
            white-space: pre-wrap;
        }
        @media (prefers-color-scheme: dark) {
            .response-box {
                background-color: #262730;
                border-left: 6px solid #ff4b4b;
            }
            .response-question { color: #fafafa; }
            .response-answer { color: #e0e0e0; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Iterate through ALL columns in order
        for col_name in df.columns:
            # We skip the internal Row_ID we generated, as it's not part of the survey data
            if col_name == "Row_ID":
                continue
                
            val = row_data[col_name]
            
            if pd.isna(val):
                continue

            # Render everything in the box style, regardless of length or type
            st.markdown(f"""
            <div class="response-box">
                <div class="response-question">{col_name}</div>
                <div class="response-answer">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- Logic: Question Analysis Mode ---
    elif view_mode == "Question Analysis View":
        st.header("Question Analysis Viewer")
        
        # Sidebar Selection for this mode
        st.sidebar.markdown("---")
        st.sidebar.subheader("Select Question")
        
        # Filter out Row_ID
        available_cols = [c for c in df.columns if c != "Row_ID"]
        
        selected_question = st.sidebar.selectbox(
            "Select Question to Analyze:",
            options=available_cols,
            index=0
        )
        
        st.markdown(f"### ❓ {selected_question}")
        st.divider()

        # CSS for the custom boxes
        st.markdown("""
        <style>
        .response-box {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            border-left: 6px solid #4e8cff;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .response-question {
            font-weight: bold;
            color: #31333F;
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        .response-answer {
            color: #1f1f1f;
            white-space: pre-wrap;
        }
        @media (prefers-color-scheme: dark) {
            .response-box {
                background-color: #262730;
                border-left: 6px solid #ff4b4b;
            }
            .response-question { color: #fafafa; }
            .response-answer { color: #e0e0e0; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Iterate through all rows
        for index, row in df.iterrows():
            name_val = row[name_col]
            answer_val = row[selected_question]
            
            if pd.isna(answer_val):
                continue

            st.markdown(f"""
            <div class="response-box">
                <div class="response-question">{name_val}</div>
                <div class="response-answer">{answer_val}</div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()