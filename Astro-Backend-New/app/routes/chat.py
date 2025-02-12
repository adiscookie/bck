# app/routes/chat.py

import os
from flask import Blueprint
from flask_socketio import emit
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

chat_bp = Blueprint('chat', __name__)

def create_claude_chain():
    """Create a LangChain conversational chain with Claude"""
    system_prompt = """"You are a highly empathetic and spiritually attuned chatbot, designed to assist users with their astronomical concerns, life challenges, health issues, and daily goal-setting. Your tone should be deeply holistic, warm, and understanding, making the user feel heard, guided, and comforted.

When responding, follow these principles:

1. Empathy First: Acknowledge the user's concerns with kindness and understanding before offering guidance.
2. Concise & Clear Answers: Avoid long-winded explanations—deliver wisdom in a simple, digestible way.
3. Relevant Puja & Ritual Recommendations: Suggest specific pujas, mantras, and remedies tailored to the user’s situation (e.g., planetary doshas, life struggles, health concerns).
4. Daily Life Guidance: Help users schedule their day in a way that aligns with planetary energies and personal well-being.
5. Lifestyle & Spiritual Tips: Offer holistic wellness advice—meditation, affirmations, mindful habits, and Vedic principles to improve overall life balance.
6. Stay in Context: Only answer queries related to astrology, pujas, spiritual well-being, and life guidance. If asked about unrelated topics (e.g., programming, tech support), gently steer the conversation back to spiritual guidance."*
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])

    model = ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0.7,
        max_tokens=1000
    )

    chain = prompt | model | StrOutputParser()
    return chain

claude_chain = create_claude_chain()

def init_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print("Client connected")
        emit('receive_message', {
            'message': 'Welcome! You are now connected to the chat assistant.',
            'sender': 'system'
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        print("Client disconnected")

    @socketio.on('send_message')
    def handle_message(data):
        try:
            user_message = data.get('message', '')
            
            if not user_message.strip():
                emit('receive_message', {
                    'message': 'Please send a valid message.',
                    'sender': 'system'
                })
                return

            print(f"User: {user_message}")
            
            response = claude_chain.invoke({"question": user_message})
            
            print(f"Claude: {response}")
            
            emit('receive_message', {
                'message': response,
                'sender': 'assistant'
            })
        
        except Exception as e:
            print(f"Error: {str(e)}")
            emit('receive_message', {
                'message': f'Error processing your request: {str(e)}',
                'sender': 'system'
            })
