import streamlit as st
import replicate
import os

# App title
st.set_page_config(page_title="🦙💬 Llama 2 Chatbot")

# Replicate Credentials
with st.sidebar:
    st.title('🦙💬 Llama 2 Chatbot')
    if 'REPLICATE_API_TOKEN' in st.secrets:
        st.success('API key already provided!', icon='✅')
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        replicate_api = st.text_input('Enter Replicate API token:', type='password')
        if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    st.subheader('Models and parameters')
    selected_model = st.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B'], key='selected_model')
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    temperature = st.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
    top_p = st.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.slider('max_length', min_value=32, max_value=4096, value=2048, step=32)
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')

# Initial questions
questions = [
    "How may I assist you today?",
    "Please provide your general information like name, city, state, country.",
    "Please provide your academic performance (grade, board, present percentage).",
    "What is your goal, financial position, and which places are you interested in?"
]

# Options to present after initial questions
options = [
    "Would you like a detailed roadmap to achieve your career goals considering your academics, financial status, and study locations?",
    "Do you want personalized career guidance based on your academic performance, financial status, and desired study locations?",
    "Do you need other specific guidance like scholarship opportunities, study programs, or financial planning?",
    "Other"
]

# Store LLM generated responses and initial questions status
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": questions[0]}]
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "show_options" not in st.session_state:
    st.session_state.show_options = False

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": questions[0]}]
    st.session_state.question_index = 0
    st.session_state.answers = []
    st.session_state.show_options = False
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating LLaMA2 response
def generate_llama2_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    try:
        output = replicate.run(
            llm, 
            input={
                "prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                "temperature": temperature,
                "top_p": top_p,
                "max_length": max_length,
                "repetition_penalty": 1
            }
        )
        return output
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "I'm sorry, I couldn't generate a response."

# Function to handle user responses and provide questions/options
def handle_user_input(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.answers.append(user_input)
    if st.session_state.question_index < len(questions) - 1:
        st.session_state.question_index += 1
        next_question = questions[st.session_state.question_index]
        st.session_state.messages.append({"role": "assistant", "content": next_question})
    else:
        st.session_state.show_options = True
        st.session_state.messages.append({"role": "assistant", "content": "Thank you for the information. Here are some options for further assistance:"})
        for option in options:
            st.session_state.messages.append({"role": "assistant", "content": option})

# Function to handle user selection of options and generate appropriate prompts
def handle_option_selection(option_selected):
    st.session_state.messages.append({"role": "user", "content": option_selected})
    # Construct the prompt based on the selected option and the user's answers
    response_prompt = f"You have the following information:\n"
    for i in range(len(questions)):
        response_prompt += f"{questions[i]} {st.session_state.answers[i]}\n"
    response_prompt += f"Based on this information, {option_selected.lower()} Assistant: "
    
    # Generate response using LLaMA2
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama2_response(response_prompt)
            if isinstance(response, list):
                for item in response:
                    st.write(item)
            else:
                st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# User-provided prompt
if prompt := st.chat_input(disabled=not replicate_api):
    handle_user_input(prompt)

# Display options and handle selection
if st.session_state.show_options:
    selected_option = st.selectbox("Select an option for further assistance:", options)
    if st.button("Submit"):
        handle_option_selection(selected_option)
        st.session_state.show_options = False

# Initial prompt to ask the first question if it's the beginning of the conversation
if st.session_state.question_index == 0 and not st.session_state.answers:
    st.session_state.messages.append({"role": "assistant", "content": questions[0]})

# Run the Streamlit app
if __name__ == "__main__":
    st.write("Welcome to the Llama 2 Chatbot!")
