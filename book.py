import streamlit as st
import json
from io import StringIO
import datetime
import pandas as pd
import plotly.express as px

# Must be the first Streamlit command
st.set_page_config(
    page_title="Personal Library Manager",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for advanced styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@300;500&display=swap');
    
    html {
        scroll-behavior: smooth;
    }
            
    .main {
        background-color: #f5f5f5;
    }
    
    .book-card {
        padding: 20px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    
    .book-card:hover {
        transform: translateY(-5px);
    }
    
    .stats-card {
        background: linear-gradient(45deg, #6a11cb, #2575fc);
        color: white!important;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
    }
    
    .stButton>button {
        border-radius: 8px;
        padding: 8px 20px;
    }
    
    h1, h2, h3 {
        font-family: 'Roboto Slab', serif!important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'library' not in st.session_state:
    st.session_state.library = []

# Rest of your functions remain the same
def save_library():
    with open('library.json', 'w') as f:
        json.dump(st.session_state.library, f)

def load_library():
    try:
        with open('library.json', 'r') as f:
            raw_data = json.load(f)
            
            # Validate library structure
            if not isinstance(raw_data, list):
                st.error("⚠️ Invalid library format: Resetting to empty library")
                st.session_state.library = []
                return
                
            # Filter valid book entries
            valid_books = []
            for idx, item in enumerate(raw_data):
                if isinstance(item, dict) and all(key in item for key in ['title', 'author', 'year', 'genre', 'read']):
                    # Convert legacy string format to boolean
                    if isinstance(item['read'], str):
                        item['read'] = item['read'].lower() == 'true'
                    valid_books.append(item)
                else:
                    st.warning(f"Removed invalid entry at position {idx}")
            
            st.session_state.library = valid_books
            st.toast(f"Loaded {len(valid_books)} valid books", icon="✅")
            
    except FileNotFoundError:
        st.session_state.library = []
    except json.JSONDecodeError:
        st.error("⚠️ Corrupted library file: Resetting to empty library")
        st.session_state.library = []

def file_handling():
    st.subheader("💾 Data Management")
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        with st.container(border=True):
            st.markdown("### 📤 Export Library")
            st.caption("Download your complete library as JSON file")
            if st.session_state.library:
                library_json = json.dumps(st.session_state.library, indent=2)
                st.download_button(
                    label="Export Data",
                    data=library_json,
                    file_name='library.json',
                    mime='application/json',
                    use_container_width=True
                )
            else:
                st.warning("No data to export")

    with col2:
        with st.container(border=True):
            st.markdown("### 📥 Import Library")
            st.caption("Upload a JSON file to import books")
            uploaded_file = st.file_uploader("Choose file", 
                                           type=['json'], 
                                           label_visibility="collapsed")
            if uploaded_file:
                try:
                    # Validate JSON structure
                    data = json.load(uploaded_file)
                    if not isinstance(data, list):
                        raise ValueError("Root element must be an array")
                        
                    # Process imported data
                    valid_books = []
                    error_count = 0
                    for idx, item in enumerate(data):
                        if isinstance(item, dict):
                            # Auto-fix common issues
                            if 'read' not in item:
                                item['read'] = False
                            if isinstance(item['read'], str):
                                item['read'] = item['read'].lower() in ['true', '1', 'yes']
                            valid_books.append(item)
                        else:
                            error_count += 1
                            
                    st.session_state.library = valid_books
                    save_library()
                    st.success(f"✅ Imported {len(valid_books)} valid books")
                    if error_count > 0:
                        st.warning(f"Skipped {error_count} invalid entries")
                        
                except Exception as e:
                    st.error(f"❌ Invalid file format: {str(e)}")

def library_view():
    st.subheader("📚 Your Digital Library")
    
    if not st.session_state.library:
        st.info("Your library is empty. Add some books!")
        return
    
    cols = st.columns(3)
    for idx, book in enumerate(st.session_state.library):
        # Fallback values for missing fields
        title = book.get('title', 'Untitled Book')
        author = book.get('author', 'Unknown Author')
        year = book.get('year', 'N/A')
        genre = book.get('genre', 'General')
        read_status = "📗 Read" if book.get('read', False) else "📘 Unread"
        
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"""
                <div class="book-card">
                    <h4>{title}</h4>
                    <p><small>by {author}</small></p>
                    <div style="color: #666;">
                        <p>📅 {year}<br>
                        🏷️ {genre}<br>
                        {read_status}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def add_book():
    with st.expander("➕ Add New Book", expanded=False):
        with st.form("add_book_form"):
            cols = st.columns([2, 1])
            with cols[0]:
                title = st.text_input("Title*", key="title")
            with cols[1]:
                year = st.number_input("Year*", 
                                    min_value=1, 
                                    max_value=datetime.datetime.now().year,
                                    step=1)
            
            cols = st.columns(2)
            with cols[0]:
                author = st.text_input("Author*", key="author")
            with cols[1]:
                genre = st.selectbox("Genre", ["Fiction", "Non-Fiction", "Science", 
                                            "History", "Biography", "Other"])
            
            read_status = st.radio("Read Status*", ["Read", "Unread"], 
                                  horizontal=True)
            
            if st.form_submit_button("📥 Add Book"):
                if not title or not author:
                    st.error("Title and Author are required fields")
                    return
                new_book = {
                    'title': title,
                    'author': author,
                    'year': int(year),
                    'genre': genre,
                    'read': read_status == "Read"
                }
                st.session_state.library.append(new_book)
                save_library()
                st.success("📚 Book added successfully!")
                st.balloons()

def remove_book():
    st.subheader("🗑️ Remove Book")
    if not st.session_state.library:
        st.warning("Library is empty")
        return
    
    df = pd.DataFrame(st.session_state.library)
    df_display = df[['title', 'author', 'year']]
    
    edited_df = st.data_editor(
        df_display,
        column_config={
            "title": "Title",
            "author": "Author",
            "year": "Year"
        },
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True
    )
    
    if st.button("Confirm Deletion"):
        if len(edited_df) < len(df):
            removed_indices = df.index.difference(edited_df.index)
            st.session_state.library = [b for i, b in enumerate(st.session_state.library) 
                                      if i not in removed_indices]
            save_library()
            st.success("✅ Selected books removed successfully!")

def search_books():
    st.subheader("🔍 Search Books")
    search_type = st.selectbox("Search by", ["Title", "Author", "Genre"])
    search_term = st.text_input("Enter search term", key="search")
    
    if search_term:
        results = []
        for book in st.session_state.library:
            target = book[search_type.lower() if search_type != "Genre" else "genre"]
            if search_term.lower() in str(target).lower():
                results.append(book)
        
        if results:
            st.success(f"📖 Found {len(results)} results:")
            cols = st.columns(3)
            for idx, book in enumerate(results):
                with cols[idx % 3]:
                    with st.container():
                        status = "📗 Read" if book['read'] else "📘 Unread"
                        st.markdown(f"""
                        <div class="book-card">
                            <h4>{book['title']}</h4>
                            <p><small>by {book['author']}</small></p>
                            <div style="color: #666;">
                                <p>📅 {book['year']} | {book['genre']}<br>
                                {status}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("No matching books found")

def display_statistics():
    st.subheader("📊 Library Statistics")
    
    if not st.session_state.library:
        st.warning("No statistics available for empty library")
        return
    
    df = pd.DataFrame(st.session_state.library)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="stats-card">'
                    '<h3>Total Books</h3>'
                    f'<h1>{len(df)}</h1></div>', 
                    unsafe_allow_html=True)
    with col2:
        read_count = df['read'].sum()
        st.markdown(f'<div class="stats-card">'
                    '<h3>Read Books</h3>'
                    f'<h1>{read_count}</h1></div>', 
                    unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stats-card">'
                    '<h3>Genres</h3>'
                    f'<h1>{df["genre"].nunique()}</h1></div>', 
                    unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Reading Progress", "Genre Distribution"])
    with tab1:
        fig = px.pie(df, names=df['read'].map({True: 'Read', False: 'Unread'}),
                    title="Read/Unread Ratio")
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        genre_counts = df['genre'].value_counts().reset_index()
        fig = px.bar(genre_counts, x='genre', y='count', 
                    color='genre', title="Books per Genre")
        st.plotly_chart(fig, use_container_width=True)

def library_view():
    st.subheader("📚 Your Digital Library")
    
    if not st.session_state.library:
        st.info("Your library is empty. Add some books!")
        return
    
    cols = st.columns(3)
    for idx, book in enumerate(st.session_state.library):
        with cols[idx % 3]:
            with st.container():
                status = "📗 Read" if book['read'] else "📘 Unread"
                st.markdown(f"""
                <div class="book-card">
                    <h4>{book['title']}</h4>
                    <p><small>by {book['author']}</small></p>
                    <div style="color: #666;">
                        <p>📅 {book['year']}<br>
                        🏷️ {book['genre']}<br>
                        {status}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def file_handling():
    st.subheader("💾 Data Management")
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        with st.container(border=True):
            st.markdown("### 📤 Export Library")
            st.caption("Download your complete library as JSON file")
            library_json = json.dumps(st.session_state.library, indent=2)
            st.download_button(
                label="Export Data",
                data=library_json,
                file_name='library.json',
                mime='application/json',
                use_container_width=True
            )
    
    with col2:
        with st.container(border=True):
            st.markdown("### 📥 Import Library")
            st.caption("Upload a JSON file to import books")
            uploaded_file = st.file_uploader("Choose file", 
                                            type=['json'], 
                                            label_visibility="collapsed")
            if uploaded_file:
                try:
                    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                    new_library = json.load(stringio)
                    st.session_state.library = new_library
                    save_library()
                    st.success("✅ Library imported successfully!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def main():
    load_library()
    st.title("📚 Digital Library Manager")
    
    # Horizontal navigation
    nav_options = {
        "🏠 Library Overview": library_view,
        "✨ Add New Book": add_book,
        "🔍 Search Books": search_books,
        "📊 Statistics": display_statistics,
        "⚙️ Manage Data": file_handling
    }
    
    selected = st.selectbox("Navigation", list(nav_options.keys()), 
                          label_visibility="collapsed")
    nav_options[selected]()
    
    # Sidebar with quick actions
    with st.sidebar:
        st.header("Quick Actions")
        if st.button("🚀 Quick Add Book"):
            add_book()
        
        st.divider()
        st.markdown("### Library Snapshot")
        if st.session_state.library:
            st.metric("Total Books", len(st.session_state.library))
            latest = st.session_state.library[-1]
            st.markdown(f"""
            **Latest Addition**:  
            🆕 {latest['title']}  
            👤 {latest['author']}
            """)
        else:
            st.info("No books in library")

if __name__ == "__main__":
    main()
