from chat_history import chat_history_manager
from agent import Agent
from prompts import PROMPTS_VERSION_ONE, PROMPTS_VERSION_TWO, DATA_ANALYST_PROMPT
from css.custom_css import inject_custom_css
from dotenv import load_dotenv
import streamlit as st
import uuid
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

load_dotenv()
st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the path to the documents folder
    documents_dir = os.path.join(current_dir, 'documents')
    
    # Construct the full path to the order_details.csv file
    csv_file_path = os.path.join(documents_dir, 'order_details.csv')
    
    # Read the CSV file
    return pd.read_csv(csv_file_path)

df = load_data()

def generate_plot(plot_type, data):
    fig, ax = plt.subplots(figsize=(8, 6))
    
    if plot_type == "Category Sales":
        category_sales = data.groupby('Category')['Total_Sale'].sum().sort_values(ascending=False)
        sns.barplot(x=category_sales.index, y=category_sales.values, ax=ax)
        ax.set_title('Total Sales by Category')
        ax.set_xlabel('Category')
        ax.set_ylabel('Total Sales ($)')
        plt.xticks(rotation=45)
    
    elif plot_type == "Marketing Channels":
        channel_counts = data['Marketing_Channel'].value_counts()
        ax.pie(channel_counts, labels=channel_counts.index, autopct='%1.1f%%')
        ax.set_title('Distribution of Orders by Marketing Channel')
    
    elif plot_type == "Daily Sales Trend":
        data['Date'] = pd.to_datetime(data['Date'])
        daily_sales = data.groupby('Date')['Total_Sale'].sum()
        ax.plot(daily_sales.index, daily_sales.values, marker='o')
        ax.set_title('Daily Sales Trend')
        ax.set_xlabel('Date')
        ax.set_ylabel('Total Sales ($)')
        plt.xticks(rotation=45)
    
    elif plot_type == "Customer Age Distribution":
        sns.histplot(data=data, x='Customer_Age', bins=20, kde=True, ax=ax)
        ax.set_title('Distribution of Customer Ages')
        ax.set_xlabel('Age')
        ax.set_ylabel('Count')
    
    elif plot_type == "Gender-wise Category Preference":
        category_gender = data.groupby(['Category', 'Customer_Gender'])['Quantity'].sum().unstack()
        category_gender.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title('Gender-wise Category Preference')
        ax.set_xlabel('Category')
        ax.set_ylabel('Quantity Sold')
        plt.legend(title='Gender')
        plt.xticks(rotation=45)
    
    elif plot_type == "Top 5 Locations by Sales":
        location_sales = data.groupby('Location')['Total_Sale'].sum().sort_values(ascending=False).head(5)
        sns.barplot(x=location_sales.index, y=location_sales.values, ax=ax)
        ax.set_title('Top 5 Locations by Sales')
        ax.set_xlabel('Location')
        ax.set_ylabel('Total Sales ($)')
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    return fig

# Inject custom CSS
inject_custom_css()

selected_prompt = DATA_ANALYST_PROMPT

# Fetch the temperature if not already fetched
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.7

# Fetch the model name if not already fetched
if 'llm_model' not in st.session_state:
    st.session_state.llm_model = "gpt-4o"

# Initialize the Agent if not already initialized
if 'agent' not in st.session_state:
    st.session_state.agent = Agent(prompt_text=selected_prompt, agent_type="strategist", Temperature=st.session_state.temperature, llm_model=st.session_state.llm_model)
    st.session_state.selected_prompt = selected_prompt  

# Sidebar for configuration
st.sidebar.title("📊 DataAnalysis Bot Settings")

# Add brief description and links in the sidebar
st.sidebar.markdown("DataAnalysis Bot: An AI-powered assistant for data visualization and analysis")
st.sidebar.markdown("[GitHub](https://github.com/yourusername/dataanalysis-bot)")  # Replace with your actual GitHub link

# Display bot configuration in sidebar
st.sidebar.subheader("🤖 Assistant Configuration")
first_sentence = """I am DataAnalysis Bot, your AI-powered data analysis assistant. I can answer questions about the dataset, generate visualizations, and provide insights based on the available data."""
st.sidebar.write(f"📝 About me: {first_sentence}")
st.sidebar.write(f"🌡️ Temperature: {st.session_state.temperature}")
st.sidebar.write(f"🧠 Model: {st.session_state.llm_model}")
st.sidebar.write("⚠️ Disclaimer: Responses are based on the provided dataset and may not cover all scenarios.")


# Initialize agent_with_chat_history in session state if not already present
if 'agent_with_chat_history' not in st.session_state:
    st.session_state.agent_with_chat_history = st.session_state.agent.get_agent_with_history()

# Initialize conversation history in session state if not already present
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Welcome! Curious about your data? Ask me anything!"}]

if 'current_plot' not in st.session_state:
    st.session_state.current_plot = None


# Create two columns with custom widths
chat_column, visualization_column = st.columns([0.6, 0.4])

# Main content area (chat interface)
with chat_column:
    st.title("📊 DataAnalysis Bot")
    st.markdown("🤖 AI-powered data analysis assistant. Ask questions about the dataset, request visualizations, or seek insights. Responses are based on the provided data and may not cover all scenarios.")

    # Create a container for the chat messages
    chat_container = st.container()

    # Create a container for the input box
    input_container = st.container()

    # Display each message in the chat
    with chat_container:
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input area for user to type their message
    with input_container:
        prompt = st.chat_input("Ask a question about the data...")

    if prompt:
        # Ensure session_id is initialized in session state
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = str(uuid.uuid4())

        # Append user message to the conversation history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            st.chat_message("user").write(prompt)

        response = st.session_state.agent_with_chat_history.invoke(
            {"input": prompt},
            config={"configurable": {"session_id": st.session_state["session_id"]}}
        )
        agent_name = "📊 DataAnalysis Bot"

        response_text = response.get('output')

        print(chat_history_manager.chat_histories)

        # Append agent's response to the conversation history
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(f"{agent_name}: {response_text}")

    # Add a footer
    st.markdown("---")

# Visualization column
with visualization_column:
    st.title("Data Visualization")
    st.header("Visualization Options")

    # Plot selection
    plot_type = st.selectbox(
        "Select a plot type",
        [
            "Category Sales", 
            "Marketing Channels", 
            "Daily Sales Trend", 
            "Customer Age Distribution", 
            "Gender-wise Category Preference", 
            "Top 5 Locations by Sales"
        ],
        key="plot_select"
    )

    # Generate plot button
    if st.button("Generate Plot", key="generate_plot"):
        fig = generate_plot(plot_type, df)
        st.session_state.current_plot = fig

    # Display the current plot if it exists
    if st.session_state.current_plot is not None:
        st.pyplot(st.session_state.current_plot)