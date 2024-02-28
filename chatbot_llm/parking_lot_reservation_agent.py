from langchain.agents import Tool, AgentType, initialize_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor
from langchain import hub
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.tools.render import render_text_description
from langchain_openai import ChatOpenAI
from langchain.tools import tool
import langchain_core
import os
import openai
import json
import streamlit as st
import sqlite3
import datetime
import json
from contextlib import contextmanager
import streamlit as st
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class ParkingLotReservationAgent:
    def __init__(self):
        self.db_path = os.getenv("DB_PATH")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.chat_history = [] 
        self.conn = sqlite3.connect(self.db_path)
        self.initialize()


 
    def process(self, query):
        try:
            response = self.agent_chain.invoke(query)
        except Exception as e:
            print("Error processing request:", e)
            response = "An error occurred while processing the request. Please try again later."
    
        return response

    def initialize(self):
        @tool("check_availability", return_direct=False)
        def check_availability(query: str) -> str:
            """Searches for available parking spaces in the system. Give the parking number in comma separated format. Once the parking spot is available."""
            try:
                # Query database to check for available parking spaces
                sql_query= """
                    SELECT parking_number 
                    FROM parking_lot
                    WHERE status = 'Unreserved'; 
                """
                cursor = self.conn.cursor()
                cursor.execute(sql_query)
                available_spaces = cursor.fetchall()
                result = ""
                for row in available_spaces:
                    result += ",".join(map(str, row)) + "\n"
                print(result)

                if available_spaces:
                    return f"Parking spaces are {result}."
                    
                else:
                    return "No available spaces available."
            except Exception as e:
                print("Error: ", e)
                return "An error occurred while checking parking availability."
            
        @tool("vehicle_reservation", return_direct=False)
        def vehicle_reservation(vehicle_id: str) -> str:
            """Once you get the vehicle id from the user as well get one unreserved parking number and make vehicle id and parking number as a comma separated input."""
            print("Vechile Info: ", vehicle_id)
            try:
                #Update parking lot status to Reserved
                update_parking_query = f"""
                    UPDATE parking_lot
                        SET status = 'Reserved', vehicle_id = NULL
                        WHERE vehicle_id = '{vehicle_id}';
                    """
                self.cursor.execute(update_parking_query)
                self.conn.commit()
                return "Your spot is reserved."
                # if query.lower() == "exit":
                #     return "Please provide the vehicle ID for exit."
                # else:
                #     return "Invalid query. Please type 'exit' to indicate vehicle exit."

            except Exception as e:
                print("Error: ", e)
                return "An error occurred during vehicle exit processing."
        
        @tool("vehicle_exit", return_direct=False)
        def vehicle_exit(query: str) -> str:
            """Process the exit of a vehicle from the parking lot. The user is prompted to provide the vehicle ID. Once the vehicle ID is received, unreserve that parking space."""
            try:
                # Check if the query is 'exit'
                if query.lower() == "exit":
                    # Prompt the user to provide the vehicle ID
                    vehicle_id = input("Please provide the vehicle ID for exit: ")
            
                    # Update the parking lot status to 'Unreserved'
                    update_parking_query = f"""
                        UPDATE parking_lot
                        SET status = 'Unreserved', vehicle_id = NULL
                        WHERE vehicle_id = '{vehicle_id}';
                    """
                    # Execute the update query
                    self.cursor.execute(update_parking_query)
                    # Commit the changes
                    self.conn.commit()

                    return "Vehicle exit processed successfully."
                else:
                    return "Invalid query. Please type 'exit' to indicate vehicle exit."
            except Exception as e:
                print("Error: ", e)
                return "An error occurred during vehicle exit processing."

            
        tools = [check_availability, vehicle_reservation, vehicle_exit]
        memory = ConversationBufferMemory(memory_key="chat_history")

        llm = ChatOpenAI(model = "gpt-4-1106-preview", temperature=0)

        self.agent_chain = initialize_agent(tools,
                               llm,
                               agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                               memory=memory,
                               verbose=True,
                               handle_parsing_errors=True)

    def __del__(self):
        # Close the SQLite connection when done 
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("Database connection closed.")

@contextmanager
def get_db_connection():
    connection = sqlite3.connect(os.getenv("DB_PATH"))
    try:
        yield connection
    finally:
        connection.close()
        
if __name__=="__main__":
    bot = ParkingLotReservationAgent()
    
    # print(bot.process("I need a parking space. Can you check if there is any Unreserved space left."))
    
    # print(bot.process("Here is my vechicle id XYZ123. Please book the parking spot for me"))
    # print(bot.process("EXIT"))
    

    # # Persistent state to store chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Chat UI layout
    st.title("Chat with Ava")

    # Display chat history
    if st.session_state.chat_history:
        for message in st.session_state.chat_history:
            st.text(message)
    
    # Text input for user message, without directly modifying session state for input clearing
    user_input = st.text_input("You:", "", key="user_input")

    # Button to send message
    send_button_clicked = st.button("Send")

    if st.button("Reset Session"):
        st.session_state.chat_history = []
        bot.chat_history = []
        bot.memory.clear()
        st.rerun()

    if send_button_clicked and user_input:
        # Append user message to chat history
        st.session_state.chat_history.append(f"You: {user_input}")
        # Get bot response and append to chat history
        bot_response = bot.process(user_input)
        bot.chat_history.append(HumanMessage(content=user_input))
        bot.chat_history.append(AIMessage(content=bot_response['output']))
        st.session_state.chat_history.append(f"Ava: {bot_response['output']}")
        # Use st.experimental_rerun() to clear the input box by rerunning the script
        st.rerun()
    
