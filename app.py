import streamlit as st
import pandas as pd
import io
import base64
from data_verification import verify_data
import time
from openai_verification import check_api_status, ai_error_message

st.set_page_config(
    page_title="Marketing Contact Verification Tool",
    page_icon="✅",
    layout="wide"
)

def get_table_download_link(df):
    """Generate a download link for the dataframe with styling preserved"""
    # Create a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Add color indicators for status
    for col in df_copy.columns:
        if col.endswith('_status'):
            # Get the base column name
            base_col = col.replace('_status', '')
            if base_col in df_copy.columns:
                # Create a new column for colored values
                df_copy[f"{base_col}_colored"] = df_copy.apply(
                    lambda row: f"✅ {row[base_col]}" if row[col] == 'Valid' else 
                    (f"⚠️ {row[base_col]}" if row[col] == 'Uncertain' else 
                     f"❌ {row[base_col]}" if row[col] == 'Invalid' else row[base_col]), 
                    axis=1
                )
                
                # Replace original column with colored version
                df_copy[base_col] = df_copy[f"{base_col}_colored"]
                # Drop the temporary column
                df_copy = df_copy.drop(f"{base_col}_colored", axis=1)
    
    # Convert to excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_copy.to_excel(writer, index=False, sheet_name='Sheet1')
        
        # Get the worksheet and set the column widths
        worksheet = writer.sheets['Sheet1']
        for i, col in enumerate(df_copy.columns):
            max_len = max(
                len(col) + 2,
                df_copy[col].astype(str).str.len().max() + 2 if len(df_copy) > 0 else 10
            )
            worksheet.set_column(i, i, max_len)
    
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="verified_contacts.xlsx">Download Excel file</a>'
    return href

def main():
    st.title("Marketing Contact Verification Tool")
    
    st.markdown("""
    This tool helps verify marketing contact information against online sources. 
    Upload your CSV or Excel file containing contact data, and this tool will:
    
    1. Check each record against online sources
    2. Highlight data as:
       - 🟢 Green: Valid information
       - 🟡 Yellow: Uncertain information
       - 🔴 Red: Incorrect information
    3. Provide the option to export the verified data with highlighting
    """)
    
    # File uploader
    uploaded_file = st.file_uploader("Upload your contact data file (CSV or Excel)", type=["csv", "xlsx"])
    
    # Option to use sample data
    use_sample_data = st.checkbox("Use sample data instead of uploading a file", value=False)
    
    df = None
    if use_sample_data:
        try:
            sample_file = "attached_assets/AI Proposal Data Sample.csv"
            df = pd.read_csv(sample_file)
            st.success("Sample data loaded successfully!")
        except Exception as e:
            st.error(f"Error loading sample data: {str(e)}")
    elif uploaded_file is not None:
        try:
            if isinstance(uploaded_file, str):
                # If it's a string (path), read directly
                if uploaded_file.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
            else:
                # If it's a file object
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
            
            st.success("File uploaded successfully!")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    # If we have data to work with, continue with the application
    if df is not None:
        # Columns to verify (updated with new column names)
        columns_to_verify = [
            "First Name", "Last Name", "Email", "Contact Job Title", "Company Name",
            "Company Address", "Company City", "Company State", "Company Country",
            "Company Postal Code", "Company Industry", "Company Phone", "Company Domain",
            "Contact LinkedIn", "Company LinkedIn"
        ]
        
        # Map any similar columns that might have different names in the dataset
        column_mapping = {
            "Company": "Company Name",
            "BYD_Industries": "Company Industry",
            "Industry": "Company Industry"
        }
        
        # Apply column mapping to match expected column names
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Check if all required columns exist
        missing_columns = [col for col in columns_to_verify if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}. Please check your file.")
        else:
            st.write("### Preview of uploaded data:")
            st.dataframe(df[columns_to_verify].head())
            
            # Verification options
            st.write("### Verification Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                verify_button = st.button("Start Verification", type="primary")
                use_ai = st.checkbox("Use AI for additional verification", value=True, 
                                    help="If unchecked, only basic verification will be performed (email format, domain existence, etc.)")
                
                # Only enable DeepSearch if AI verification is enabled
                deep_search_disabled = not use_ai
                use_deep_search = st.checkbox("Enable DeepSearch", value=False, disabled=deep_search_disabled,
                                    help="Uses more powerful AI models (GPT-4) to perform deeper verification of contacts, especially job titles and LinkedIn profiles. May require more time and API quota. Requires AI verification to be enabled.")
                
            with col2:
                max_rows = st.number_input(
                    "Maximum rows to verify (0 for all)", 
                    min_value=0, 
                    max_value=len(df), 
                    value=min(10, len(df))
                )
            
            # Check OpenAI API status if AI verification is requested
            if use_ai:
                api_status = check_api_status()
                if ai_error_message:
                    st.warning(ai_error_message)
                    # Update the checkbox if there are API issues
                    if not api_status:
                        use_ai = False
                        use_deep_search = False
                        st.info("AI verification has been automatically disabled. Basic verification will still be performed.")
            else:
                # If AI is disabled, disable deep search as well
                use_deep_search = False
            
            if verify_button:
                # Show verification info based on settings
                if use_ai and use_deep_search:
                    st.info("DeepSearch mode is enabled. The verification will use GPT-4 for more thorough analysis of contact information, especially for job titles and LinkedIn profiles. This may take longer but will provide more accurate results.")
                
                # If max_rows is 0, verify all rows
                rows_to_verify = len(df) if max_rows == 0 else max_rows
                
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Start verification
                status_text.text("Starting verification process...")
                
                # Process in batches to show progress
                verified_df = df.copy()
                
                # Keep track of rows being processed
                rows_to_process = min(rows_to_verify, len(df))
                
                for i in range(rows_to_process):
                    # Update progress
                    progress = int((i + 1) / rows_to_process * 100)
                    progress_bar.progress(progress)
                    
                    # Show more detailed status message based on verification mode
                    if use_ai and use_deep_search:
                        status_text.text(f"Verifying row {i+1} of {rows_to_process} with DeepSearch...")
                    elif use_ai:
                        status_text.text(f"Verifying row {i+1} of {rows_to_process} with AI...")
                    else:
                        status_text.text(f"Verifying row {i+1} of {rows_to_process} with basic checks...")
                    
                    # Verify the current row
                    row_data = df.iloc[i:i+1].copy()
                    verified_row = verify_data(row_data, columns_to_verify, use_ai, use_deep_search)
                    
                    # Update the dataframe with verified data
                    for col in verified_row.columns:
                        verified_df.loc[verified_df.index[i], col] = verified_row.iloc[0][col]
                    
                    # Small delay to make progress visible
                    time.sleep(0.1)
                
                # Complete
                progress_bar.progress(100)
                status_text.text("Verification complete!")
                
                # Display results
                st.write("### Verification Results")
                
                # Create a styled dataframe for display
                display_df = verified_df.copy()
                
                # Get only the columns we need for display
                display_columns = []
                for col in columns_to_verify:
                    display_columns.append(col)
                    if f"{col}_status" in display_df.columns:
                        display_columns.append(f"{col}_status")
                
                # Function to color cells based on status
                def color_cells(row):
                    styles = {}
                    for col in columns_to_verify:
                        status_col = f"{col}_status"
                        if status_col in row.index:
                            if row[status_col] == 'Valid':
                                styles[col] = 'background-color: #9CFF9C'  # Light green
                            elif row[status_col] == 'Uncertain':
                                styles[col] = 'background-color: #FFFFB5'  # Light yellow
                            elif row[status_col] == 'Invalid':
                                styles[col] = 'background-color: #FFCCCB'  # Light red
                    return pd.Series(styles)
                
                # Apply styling
                styled_df = display_df[display_columns].style.apply(color_cells, axis=1)
                
                # Display styled dataframe
                st.dataframe(styled_df)
                
                # Download link
                st.markdown(get_table_download_link(display_df), unsafe_allow_html=True)
                
                # Summary statistics
                st.write("### Verification Summary")
                
                summary_data = {}
                for col in columns_to_verify:
                    status_col = f"{col}_status"
                    if status_col in display_df.columns:
                        valid_count = (display_df[status_col] == 'Valid').sum()
                        uncertain_count = (display_df[status_col] == 'Uncertain').sum()
                        invalid_count = (display_df[status_col] == 'Invalid').sum()
                        
                        summary_data[col] = {
                            'Valid': valid_count,
                            'Uncertain': uncertain_count,
                            'Invalid': invalid_count
                        }
                
                # Convert to dataframe for display
                summary_df = pd.DataFrame(summary_data).T
                summary_df['Total'] = summary_df.sum(axis=1)
                summary_df['Valid %'] = (summary_df['Valid'] / summary_df['Total'] * 100).round(1)
                
                st.dataframe(summary_df)

if __name__ == "__main__":
    main()