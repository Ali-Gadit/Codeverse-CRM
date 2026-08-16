# imports
import streamlit as st
import pandas as pd
import os
import database as db
import html
import urllib.parse
from io import BytesIO
import datetime

# Initialize Database
db.init_db()

# Page configuration for a professional wide dashboard layout
st.set_page_config(
    page_title="Codeverse CRM Workspace",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium UI styling (Indigo theme, custom KPI Cards, and Login Screen)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Global typeface bindings */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Soft background color for modern dashboard look */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Login Page Container */
    .login-container {
        max-width: 450px;
        margin: 80px auto 10px auto;
        padding: 40px;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .login-header {
        font-size: 26px;
        font-weight: 800;
        color: #6366F1;
        margin-bottom: 8px;
    }
    .login-subtitle {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 20px;
    }
    
    /* Sidebar header styling */
    .sidebar-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1E1B4B;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #E2E8F0;
    }
    
    /* Dynamic KPI Card Layout */
    .kpi-row {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 25px;
    }
    .kpi-card {
        flex: 1 1 150px;
        min-width: 150px;
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        border: 1px solid #E2E8F0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
    }
    .kpi-card.total { border-left: 5px solid #6366F1; }
    .kpi-card.to_action { border-left: 5px solid #F59E0B; }
    .kpi-card.acted { border-left: 5px solid #3B82F6; }
    .kpi-card.converted { border-left: 5px solid #10B981; }
    .kpi-card.failed { border-left: 5px solid #EF4444; }
    .kpi-card.rate { border-left: 5px solid #14B8A6; }
    
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    
    /* Control element visual enhancements */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }
    div[data-baseweb="select"] {
        border-radius: 8px !important;
    }
    button[kind="secondary"] {
        border-radius: 8px !important;
    }
    button[kind="primary"] {
        background-color: #6366F1 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    button[kind="primary"]:hover {
        background-color: #4F46E5 !important;
    }
    
    /* Section and Group Headings */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1E1B4B;
        margin-top: 25px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Custom Scrollbar for lead details container */
    .lead-details-scroll-container::-webkit-scrollbar {
        width: 6px;
    }
    .lead-details-scroll-container::-webkit-scrollbar-track {
        background: #F1F5F9;
        border-radius: 4px;
    }
    .lead-details-scroll-container::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 4px;
    }
    .lead-details-scroll-container::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Authentication State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'email' not in st.session_state:
    st.session_state['email'] = None
if 'selected_table_name' not in st.session_state:
    st.session_state['selected_table_name'] = None
if 'selected_row_idx' not in st.session_state:
    st.session_state['selected_row_idx'] = None

# Check URL parameters for persistent login token
if st.query_params.get('auth') == 'true':
    st.session_state['logged_in'] = True
    st.session_state['role'] = st.query_params.get('role', 'caller')
    st.session_state['email'] = st.query_params.get('email', 'caller@codeverse.com')

# AUTHENTICATION ROUTINE
if not st.session_state['logged_in']:
    # Center the login panel
    _, col_login, _ = st.columns([1, 1.6, 1])
    
    with col_login:
        st.markdown("""
            <div class="login-container">
                <div class="login-header">🚀 Codeverse CRM</div>
                <div class="login-subtitle">Customer Relationship Management Portal</div>
            </div>
        """, unsafe_allow_html=True)
        
        # User credentials form fields
        email_input = st.text_input("Registered Email", placeholder="email@example.com")
        password_input = st.text_input("Portal Password", type="password", placeholder="Enter password")
        
        st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
        
        # Validation checks
        if st.button("Sign In", use_container_width=True, type="primary"):
            email_val = email_input.strip()
            if email_val == "aligadit9192@gmail.com" and password_input == "CODEVERSE_AL1":
                st.session_state['logged_in'] = True
                st.session_state['role'] = 'admin'
                st.session_state['email'] = email_val
                st.query_params["auth"] = "true"
                st.query_params["role"] = "admin"
                st.query_params["email"] = email_val
                st.success("Admin Authentication successful! Redirecting...")
                st.rerun()
            elif email_val == "caller@codeverse.com" and password_input == "CALLER_123":
                st.session_state['logged_in'] = True
                st.session_state['role'] = 'caller'
                st.session_state['email'] = email_val
                st.query_params["auth"] = "true"
                st.query_params["role"] = "caller"
                st.query_params["email"] = email_val
                st.success("Agent Authentication successful! Redirecting...")
                st.rerun()
            else:
                st.error("Access Denied: Invalid email or password.")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- LOGGED IN USER INTERFACE ---
    
    role = st.session_state.get('role', 'caller')
    
    # 1. SIDEBAR CONFIGURATION
    with st.sidebar:
        st.markdown('<div class="sidebar-header">👤 Logged In Profile</div>', unsafe_allow_html=True)
        role_display = "Administrator" if role == 'admin' else "Agent / Cold Caller"
        st.write(f"**Email:** `{st.session_state.get('email', '')}`")
        st.write(f"**Role:** {role_display}")
        
        # Logout trigger
        if st.button("Sign Out of Portal", type="secondary", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['role'] = None
            st.session_state['selected_table_name'] = None
            st.query_params.clear()
            st.rerun()
            
        if role == 'admin':
            st.markdown('<br><div class="sidebar-header">📥 Upload CRM Data</div>', unsafe_allow_html=True)
            # Import CSV or Excel files
            uploaded_file = st.file_uploader(
                "Upload leads list:", 
                type=["csv", "xlsx"], 
                accept_multiple_files=False,
                help="Accepted file types: CSV, Excel (.xlsx)"
            )
            
            if uploaded_file is not None:
                # Check if this exact file was already uploaded to prevent duplicates on rerun
                if 'uploaded_file_id' not in st.session_state or st.session_state['uploaded_file_id'] != uploaded_file.file_id:
                    try:
                        # Load the file into a DataFrame
                        file_ext = os.path.splitext(uploaded_file.name)[-1].lower()
                        if file_ext == ".csv":
                            df_upload = pd.read_csv(uploaded_file)
                        else:
                            df_upload = pd.read_excel(uploaded_file)
                        
                        # Verify that dataset is not blank
                        if df_upload.empty:
                            st.error("The uploaded file does not contain any records.")
                        else:
                            # Save contents to SQLite dynamic table
                            new_table_name = db.save_dataframe(df_upload, uploaded_file.name)
                            st.session_state['selected_table_name'] = new_table_name
                            st.session_state['uploaded_file_id'] = uploaded_file.file_id
                            st.success(f"Successfully imported '{uploaded_file.name}'!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error parsing database file: {e}")
                
        st.markdown('<br><div class="sidebar-header">📂 Loaded Datasets</div>', unsafe_allow_html=True)
        available_tables = db.get_tables()
        
        if available_tables:
            # Format display labels for selectbox dropdown
            table_options = {t['table_name']: f"📁 {t['display_name']} ({t['uploaded_at'].split()[0]})" for t in available_tables}
            
            # Select table
            current_selected = st.session_state['selected_table_name']
            if current_selected not in table_options:
                current_selected = available_tables[0]['table_name']
                st.session_state['selected_table_name'] = current_selected
                
            selected_table_name = st.selectbox(
                "Select active dataset:",
                options=list(table_options.keys()),
                format_func=lambda x: table_options[x],
                index=list(table_options.keys()).index(current_selected)
            )
            
            # Update state on change
            if selected_table_name != st.session_state['selected_table_name']:
                st.session_state['selected_table_name'] = selected_table_name
                st.rerun()
                


            # Drop table from SQLite catalog
            if role == 'admin':
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🗑️ Delete Current Dataset", type="secondary", use_container_width=True):
                    db.delete_table(selected_table_name)
                    st.session_state['selected_table_name'] = None
                    st.toast("Dataset permanently deleted!")
                    st.rerun()
        else:
            st.info("No datasets loaded. Upload a file above to begin.")
            st.session_state['selected_table_name'] = None

    # 2. MAIN CRM CONTAINER
    st.markdown("""
        <div style="margin-bottom: 25px;">
            <span style="font-size: 2.2rem; font-weight: 800; color: #1E1B4B;">🚀 Codeverse CRM Portal</span>
            <p style="font-size: 1rem; color: #64748B; margin-top: 5px;">
                Manage pipeline leads, update action status, filter dynamic tables, prune data records, and export CRM logs.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Active pipeline workspace
    active_table = st.session_state['selected_table_name']
    if active_table:
        # Due Callbacks Alert System
        due_callbacks = db.get_due_callbacks()
        if due_callbacks:
            active_dues = [cb for cb in due_callbacks if cb['table_name'] == active_table]
            if active_dues:
                st.markdown('<div class="section-title" style="color: #EF4444; margin-bottom: 5px;">🔔 Action Required: Due Callbacks</div>', unsafe_allow_html=True)
                for cb in active_dues:
                    time_str = cb['callback_time']
                    try:
                        time_obj = datetime.datetime.fromisoformat(time_str)
                        time_str = time_obj.strftime("%b %d, %Y %I:%M %p")
                    except:
                        pass
                    st.warning(f"**Lead ID #{cb['_crm_id']}**: {cb['callback_notes']} *(Scheduled for: {time_str})*")
                    
        df_active = db.get_table_data(active_table)
        
        if df_active is not None and not df_active.empty:
            # CRM Pipeline stage metrics
            # Get all available statuses dynamically
            all_statuses = db.get_statuses()
            
            total_leads = len(df_active)
            status_counts = {s: len(df_active[df_active['status'] == s]) for s in all_statuses}
            converted_count = status_counts.get('Converted', 0)
            conversion_rate = (converted_count / total_leads * 100) if total_leads > 0 else 0.0
            
            # Display Styled KPI Widget Cards
            kpi_html = f'<div class="kpi-row"><div class="kpi-card total"><div class="kpi-title">📋 Total Leads</div><div class="kpi-value">{total_leads}</div></div>'
            
            color_map = {'TO action': 'to_action', 'Acted': 'acted', 'Converted': 'converted', 'Failed': 'failed'}
            icon_map = {'TO action': '⏳', 'Acted': '⚙️', 'Converted': '🎉', 'Failed': '❌'}
            
            for s in all_statuses:
                cls_name = color_map.get(s, 'to_action') # fallback
                icon = icon_map.get(s, '📌')
                kpi_html += f'<div class="kpi-card {cls_name}"><div class="kpi-title">{icon} {s}</div><div class="kpi-value">{status_counts[s]}</div></div>'
                
            kpi_html += f'<div class="kpi-card rate"><div class="kpi-title">📈 Conversion</div><div class="kpi-value">{conversion_rate:.1f}%</div></div></div>'
            
            st.markdown(kpi_html, unsafe_allow_html=True)
            
            # Filtering section
            st.markdown('<div class="section-title">🔍 Interactive Filters & Keyword Search</div>', unsafe_allow_html=True)
            
            # Text-based keyword search filter
            search_query = st.text_input("Search lead record fields:", placeholder="Type a name, email, country, or company to search...")
            
            # Status Filter Button Section
            st.markdown("<p style='font-size: 0.9rem; font-weight: 600; color: #475569; margin-bottom: 8px;'>Filter by Pipeline Status:</p>", unsafe_allow_html=True)
            
            # Initialize active filter state in session_state if not present
            if 'active_status_filter' not in st.session_state:
                st.session_state['active_status_filter'] = 'All'
                
            btn_labels = ['All'] + all_statuses + ['Scheduled']
            cols_per_row = 6
            for row_idx in range(0, len(btn_labels), cols_per_row):
                row_labels = btn_labels[row_idx:row_idx+cols_per_row]
                cols = st.columns(len(row_labels))
                for i, label in enumerate(row_labels):
                    with cols[i]:
                        is_active = (st.session_state['active_status_filter'] == label)
                        if label == 'All':
                            btn_text = "📋 Show All Leads"
                        elif label == 'Scheduled':
                            btn_text = "📅 Scheduled"
                        else:
                            btn_text = f"{icon_map.get(label, '📌')} {label}"
                            
                        if st.button(btn_text, type="primary" if is_active else "secondary", use_container_width=True, key=f"filter_btn_{label}"):
                            st.session_state['active_status_filter'] = label
                            st.rerun()
            
            # Apply active filters to DataFrame
            df_display = df_active.copy()
            active_filter = st.session_state['active_status_filter']
            
            if active_filter == 'Scheduled':
                if 'callback_time' in df_display.columns:
                    df_display = df_display[
                        df_display['callback_time'].notna() & 
                        (df_display['callback_time'].astype(str).str.strip() != '') & 
                        (df_display['callback_time'].astype(str).str.strip() != 'None')
                    ]
                else:
                    df_display = df_display.iloc[0:0]
            elif active_filter != 'All':
                df_display = df_display[df_display['status'] == active_filter]
            
            if search_query.strip():
                df_display = df_display[df_display.astype(str).apply(
                    lambda row: row.str.contains(search_query, case=False).any(), axis=1
                )]
            
            # Check if selection index is valid for layout
            has_selection = (st.session_state['selected_row_idx'] is not None and 
                             st.session_state['selected_row_idx'] < len(df_display))
            
            # Split page into columns (Master-Detail layout) if a row is selected
            if has_selection:
                col_left, col_right = st.columns([1.7, 1.3], gap="large")
            else:
                col_left = st.container()
                col_right = None

            # Render Leads Data Table in left container/column
            with col_left:
                st.markdown(f'<div class="section-title">📊 Leads Registry ({len(df_display)} matched)</div>', unsafe_allow_html=True)
                if df_display.empty:
                    st.warning("No lead records match the active search filters.")
                    selection = {"rows": []}
                else:
                    # Render using native st.dataframe with single-row selection enabled
                    selection = st.dataframe(
                        df_display,
                        column_config={
                            "_crm_id": st.column_config.NumberColumn(
                                "ID",
                                help="Lead identification number",
                                width="small",
                                format="%d"
                            ),
                            "status": st.column_config.Column(
                                "Status",
                                width="medium"
                            )
                        },
                        hide_index=True,
                        use_container_width=True,
                        on_select="rerun",
                        selection_mode="single-row"
                    )
            
            # Parse selection state
            selected_rows = []
            if selection:
                if isinstance(selection, dict):
                    sel_dict = selection.get("selection", {})
                    if isinstance(sel_dict, dict):
                        selected_rows = sel_dict.get("rows", [])
                    else:
                        selected_rows = selection.get("rows", [])
                elif hasattr(selection, "selection"):
                    sel_obj = selection.selection
                    if isinstance(sel_obj, dict):
                        selected_rows = sel_obj.get("rows", [])
                    elif hasattr(sel_obj, "rows"):
                        selected_rows = sel_obj.rows
                elif hasattr(selection, "rows"):
                    selected_rows = selection.rows
            
            # Check if selection changed, if so rerun to update layout columns
            new_idx = selected_rows[0] if selected_rows else None
            if new_idx != st.session_state['selected_row_idx']:
                st.session_state['selected_row_idx'] = new_idx
                st.rerun()

            # Render Lead Detail & Action Panel on the right side of the main container
            if col_right is not None and new_idx is not None and new_idx < len(df_display):
                with col_right:
                    selected_row = df_display.iloc[new_idx]
                    crm_id = int(selected_row['_crm_id'])
                    current_status = selected_row['status']
                    
                    st.markdown('<div class="section-title">✏️ Lead Detail & Actions</div>', unsafe_allow_html=True)
                    
                    # Show lead summary card
                    st.markdown(f'<div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 15px; border-left: 5px solid #6366F1;"><strong style="color: #1E1B4B; font-size: 0.95rem;">Lead ID #{crm_id}</strong><p style="color: #64748B; font-size: 0.8rem; margin: 3px 0 0 0;">Update pipeline stage or delete this lead.</p></div>', unsafe_allow_html=True)
                    
                    # Render details card in a beautiful scrollable box
                    details_html = ""
                    for col in selected_row.index:
                        if col not in ('_crm_id', 'status', 'callback_time', 'callback_notes') and pd.notna(selected_row[col]):
                            col_name = html.escape(str(col))
                            val = html.escape(str(selected_row[col]))
                            details_html += f'<div style="margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #F1F5F9; font-size: 0.85rem;"><div style="font-weight: 600; color: #475569; margin-bottom: 2px;">{col_name}</div><div style="color: #0F172A; word-break: break-word; font-weight: 500;">{val}</div></div>'
                    
                    st.markdown(f'<div class="lead-details-scroll-container" style="max-height: 380px; overflow-y: auto; padding: 12px; border-radius: 8px; border: 1px solid #E2E8F0; background-color: #F8FAFC; margin-bottom: 15px; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.03);">{details_html}</div>', unsafe_allow_html=True)
                    
                    st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
                    
                    # Status dropdown selectbox
                    status_options = db.get_statuses()
                    current_idx = status_options.index(current_status) if current_status in status_options else 0
                    new_status = st.selectbox(
                        "Move pipeline stage to:",
                        options=status_options,
                        index=current_idx,
                        key=f"lead_status_{crm_id}"
                    )
                    
                    st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
                    col_btn_update, col_btn_delete = st.columns(2)
                    with col_btn_update:
                        if st.button("Apply Status", type="primary", use_container_width=True):
                            db.update_status(active_table, crm_id, new_status)
                            st.toast("Status updated successfully!")
                            st.rerun()
                    with col_btn_delete:
                        if role == 'admin':
                            if st.button("Delete Lead", type="secondary", use_container_width=True):
                                db.delete_row(active_table, crm_id)
                                st.toast("Lead record deleted!")
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 0.85rem; font-weight: 600; color: #475569;'>Create New Custom Status</p>", unsafe_allow_html=True)
                    
                    col_custom_input, col_custom_btn = st.columns([2, 1])
                    with col_custom_input:
                        custom_new_status = st.text_input("New status label", placeholder="e.g. Retry", key=f"new_custom_status_{crm_id}", label_visibility="collapsed")
                    with col_custom_btn:
                        if st.button("Add", type="secondary", use_container_width=True):
                            if custom_new_status.strip():
                                db.add_custom_status(custom_new_status.strip())
                                st.toast(f"Added new status: {custom_new_status.strip()}")
                                st.rerun()
                            else:
                                st.error("Enter a name.")

                    st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 0.85rem; font-weight: 600; color: #475569;'>📅 Schedule Callback</p>", unsafe_allow_html=True)
                    
                    # Add current callback time if exists
                    curr_cb_time = selected_row.get('callback_time', '')
                    curr_cb_notes = selected_row.get('callback_notes', '')
                    if pd.notna(curr_cb_time) and str(curr_cb_time).strip() and str(curr_cb_time) != 'None':
                        try:
                            time_obj = datetime.datetime.fromisoformat(str(curr_cb_time))
                            disp_time = time_obj.strftime("%b %d, %Y %I:%M %p")
                        except:
                            disp_time = curr_cb_time
                        st.info(f"**Scheduled:** {disp_time}\n\n**Notes:** {curr_cb_notes}")
                        
                    cb_notes = st.text_input("Callback Notes (Optional)", placeholder="e.g. Owner returning tomorrow", key=f"cb_notes_{crm_id}")
                    
                    col_cb1, col_cb2, col_cb3 = st.columns(3)
                    with col_cb1:
                        if st.button("+1 Hour", use_container_width=True, key=f"cb_1h_{crm_id}"):
                            dt = (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()
                            db.update_callback(active_table, crm_id, dt, cb_notes)
                            st.toast("Scheduled for 1 hour from now!")
                            st.rerun()
                    with col_cb2:
                        if st.button("Tomorrow", use_container_width=True, key=f"cb_1d_{crm_id}"):
                            dt = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
                            db.update_callback(active_table, crm_id, dt, cb_notes)
                            st.toast("Scheduled for tomorrow!")
                            st.rerun()
                    with col_cb3:
                        if st.button("Clear", use_container_width=True, key=f"cb_clr_{crm_id}"):
                            db.update_callback(active_table, crm_id, None, None)
                            st.toast("Callback cleared!")
                            st.rerun()
                            
                    with st.expander("Or Pick Custom Date/Time"):
                        d = st.date_input("Date", key=f"cb_d_{crm_id}")
                        col_h, col_m = st.columns(2)
                        with col_h:
                            h = st.number_input("Hour (0-23)", min_value=0, max_value=23, value=0, format="%02d", key=f"cb_h_{crm_id}")
                        with col_m:
                            m = st.number_input("Minute (0-59)", min_value=0, max_value=59, value=0, format="%02d", key=f"cb_m_{crm_id}")
                        
                        if st.button("Set Custom Time", use_container_width=True, key=f"cb_cust_{crm_id}"):
                            t = datetime.time(h, m)
                            dt = datetime.datetime.combine(d, t).isoformat()
                            db.update_callback(active_table, crm_id, dt, cb_notes)
                            st.toast("Custom callback scheduled!")
                            st.rerun()

            if role == 'admin':
                # Column Removal Panel at the bottom
                custom_cols = [c for c in df_active.columns if c not in ('_crm_id', 'status', 'callback_time', 'callback_notes')]
                if custom_cols:
                    st.markdown('<br><div class="section-title">🗑️ Delete Columns Permanently</div>', unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 0.85rem; color: #64748B; margin-bottom: 8px;'>Prune custom columns from the SQLite database table:</p>", unsafe_allow_html=True)
                    cols_layout = st.columns(len(custom_cols) if len(custom_cols) < 8 else 8)
                    for idx, col_name in enumerate(custom_cols):
                        col_pos = idx % 8
                        with cols_layout[col_pos]:
                            if st.button(f"✕ {col_name}", key=f"drop_btn_{col_name}", use_container_width=True, help=f"Delete column '{col_name}'"):
                                db.delete_column(active_table, col_name)
                                st.toast(f"Dropped column '{col_name}'!")
                                st.rerun()

                # Data Export & Download Block
                st.markdown('<br><div class="section-title">📥 Export Pipeline Data</div>', unsafe_allow_html=True)
                col_exp_1, col_exp_2 = st.columns([1, 2])
                
                with col_exp_1:
                    export_format = st.radio("Choose Output Format:", ["CSV", "Excel"], horizontal=True)
                    clean_export = st.checkbox("Strip system tracker IDs (`_crm_id`) from export file", value=True)
                
                with col_exp_2:
                    # Strip system columns if requested
                    export_df = df_display.copy()
                    if clean_export and '_crm_id' in export_df.columns:
                        export_df = export_df.drop(columns=['_crm_id'])
                    
                    buffer = BytesIO()
                    if export_format == "CSV":
                        export_df.to_csv(buffer, index=False)
                        file_name = f"crm_leads_export_{active_table}.csv"
                        mime_type = "text/csv"
                    else:
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            export_df.to_excel(writer, index=False)
                        file_name = f"crm_leads_export_{active_table}.xlsx"
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    
                    buffer.seek(0)
                    
                    st.markdown("<div style='padding-top: 15px;'>", unsafe_allow_html=True)
                    st.download_button(
                        label=f"💾 Download CRM Export ({export_format})",
                        data=buffer,
                        file_name=file_name,
                        mime=mime_type,
                        use_container_width=True,
                        type="primary"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("The selected dataset is empty.")
    else:
        # Blank state instructions
        st.markdown("""
            <div style="background-color: #ffffff; padding: 40px; border-radius: 16px; border: 1px dashed #CBD5E1; text-align: center; margin-top: 30px;">
                <div style="font-size: 3rem; margin-bottom: 20px;">📂</div>
                <h3 style="color: #1E1B4B; margin-bottom: 10px; font-weight: 700;">No CRM Dataset Active</h3>
                <p style="color: #64748B; max-width: 500px; margin: 0 auto 30px auto; font-size: 0.95rem; line-height: 1.6;">
                    Upload a CSV or XLSX file containing customer data using the sidebar menu on the left to start organizing your pipeline.
                </p>
                <div style="display: inline-flex; flex-direction: column; align-items: flex-start; text-align: left; background-color: #F8FAFC; padding: 25px; border-radius: 12px; border: 1px solid #E2E8F0;">
                    <strong style="color: #0F172A; margin-bottom: 8px;">Quick Start Guide:</strong>
                    <ol style="color: #475569; padding-left: 20px; font-size: 0.9rem; margin-bottom: 0; line-height: 1.8;">
                        <li>Drag & drop your leads CSV or Excel spreadsheet into the sidebar file uploader.</li>
                        <li>The system automatically loads records and appends a status column set to <code style="background-color: #E2E8F0; padding: 2px 6px; border-radius: 4px;">TO action</code>.</li>
                        <li>Filter leads dynamically by pipeline stage or use full-text search across all fields.</li>
                        <li>Change lead stages, delete individual rows, or prune entire columns from the table.</li>
                        <li>Export and download your customized pipeline spreadsheet at any time.</li>
                    </ol>
                </div>
            </div>
        """, unsafe_allow_html=True)