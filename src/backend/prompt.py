def get_system_prompt(user_name):
    with open("src/backend/system_prompt.txt", "r") as file:
        system_prompt = file.read()
        system_prompt = system_prompt.replace("<USER_NAME>", user_name)
        return system_prompt

def get_user_prompt(message, resume, context, chat_history):
    user_prompt = f"""
    You are responding to a recruiter's question.
    """
        
    # Add chat history to user prompt if available
    if chat_history:
        user_prompt += f"""
            ## PREVIOUS CONVERSATION SUMMARY
            **chat history to give you context of the conversation so far**
            ```
            {chat_history}
            ```
            """
        
    user_prompt += f"""
    ## CURRENT QUESTION
    **If question not clear, try to infer from chat history.**
    {message}

    ## RESUME INFORMATION
    **Address resume only if relevant to the question.**
    ```
    {resume}
    ```
    """

    # Add context at the end with better formatting
    context_text = "\n".join(context) if isinstance(context, list) else context
    user_prompt += f"""
            ## RELEVANT CODE/PROJECT CONTEXT
            **Address code in context only if relevant to the question.**
            ```
            {context_text}
            ```
            """
    
    return user_prompt
