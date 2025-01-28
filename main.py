import streamlit as st
import json
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import re
genai.configure(api_key="AIzaSyCZpc1GCd6MoIykwGO-jjdrpdQRnnzXaHc")
model = genai.GenerativeModel("gemini-1.5-flash")
def summarize_arabic_text_by_word_count(text, np, search_word):
    prompt = f"""
    I searched for news using the keyword "{search_word}" and retrieved the following content:
    
    {text}
    
    Please rewrite this content in Arabic, making it more informative and structured as a news article. Divide it into {np} paragraph, with approximately {1000 * np} words in total. Use a professional and formal tone, and add two blank spaces between each paragraph for clear formatting. Make it appear as original news content rather than a summarized version.
 if you have linkes for refrances just add them، if you cant write just dont write any thing dont say things like i cant genrate this content, if the  keyword not related say "لا اجد اجابه مناسبه في هذه المواقع"   """

    # Generate the response using the model
    response = model.generate_content(prompt)
    text = response.candidates[0].content.parts[0].text
    return(text)
np_map = {
    '1 month' : 1 , 
    '3 months' : 2, 
    '6 months' : 3, 
    '9 months'  : 4
}
# Database file path
DB_FILE = "database.json"
# Function to read the database
def read_database():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
def search_articles(country, website, category, db, search_word,duration):
    """
    Retrieves articles from the database based on the selected country, website, category, and search word.

    Args:
    - country (str): Selected country.
    - website (str): Selected website.
    - category (str): Selected category.
    - db (dict): The database.
    - search_word (str): The word to search in article titles.

    Returns:
    - list: List of articles matching the criteria.
    """
    res = []
    for i in website:
    # Check if country and website exist in the database
        if country in db and i in db[country].keys():
            # Fetch all articles for the selected website
            articles = db[country][i]

            # Filter articles based on the search word in the title
            filtered_articles = [
                article for article in articles if search_word in article["artical_name"]
            ]
            
            res= res+ filtered_articles
        else:
            res= res+ []
    if len(res) >= 5:
        # Get first 5 articles and combine their content
        text_content = "\n".join([article["contnet"] for article in res[:5]])
        return summarize_arabic_text_by_word_count(text_content, np_map[duration], search_word)
    elif len(res) > 0:
        # Return all articles if less than 5
        text_content = "\n".join([article["contnet"] for article in res])
        return summarize_arabic_text_by_word_count(text_content, np_map[duration], search_word)
    else:
        return "لا توجد نتائج متاحة"

# Load the database
db = read_database()

# Extract countries and their websites with article counts
countries = list(db.keys())
categories = {country: list(db[country].keys()) for country in countries}

# Generate article counts for each website
websites_info = {
    country: {website: len(articles) for website, articles in db[country].items()}
    for country in db
}

# Streamlit interface
st.markdown(
    """
    <style>
    .stMarkdown, .stTextInput, .stSelectbox, .stMultiselect, .stButton button {
        font-size: 18px;
    }
    .stTextArea textarea {
        font-size: 18px;
        height: auto !important;
        overflow: hidden !important;
        resize: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("News Search App")

# Sidebar for country and category selection
st.sidebar.header("Selection Menu")
country = st.sidebar.selectbox("Select Country", countries)

if country:
    category = st.sidebar.selectbox("Select Category",['سياسة', 'اقتصاد', 'رياضة'])

    # Display websites as checkboxes with article counts
    st.subheader(f"Websites for {country}")
    websites_available = websites_info[country]
    websites_selected = [
        site for site, count in websites_available.items() if st.checkbox(f"{site} ({count} articles)")
    ]
else:
    websites_selected = []

# Word input
word = st.text_input("Enter Word to Search")

# Duration selection
durations = ["1 month", "3 months", "6 months", "9 months"]
duration = st.selectbox("Select Duration", durations)

# Validation logic
all_fields_filled = (
    country
    and category
    and websites_selected
    and word.strip()
    and duration
)

# Search button
if not all_fields_filled:
    st.warning("Please complete all fields to enable the search.")
else:
    if st.button("Search"):
        # Replace 'your_function' with the actual function to search articles
        result = f"Search results for '{word}' in {country} on {', '.join(websites_selected)} ({duration})"
        print(country)
        articles = search_articles(country, websites_selected, category, db, word.strip(),duration)
        
        # Display articles text
        if articles:
            st.markdown(
                f"""
                <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; font-size: 18px;">
                    {articles}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Add download button for text file
            def create_formatted_text():
                # Create formatted text content
                formatted_text = f"""Search Results
------------------------
Search Word: {word}
Country: {country}
Category: {category}
Websites: {', '.join(websites_selected)}
Duration: {duration}

Content:
------------------------
{articles}
"""
                return formatted_text.encode()

            # Add download button
            st.download_button(
                label="Download as Text",
                data=create_formatted_text(),
                file_name=f"{word}_search_results.txt",
                mime="text/plain"
            )
            
        else:
            st.warning(f"No articles found for {websites_selected} in {category} matching '{word}'.")
