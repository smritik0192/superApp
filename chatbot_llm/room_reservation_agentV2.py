from langchain.agents import Tool, AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentExecutor
import langchain_core
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.tools.render import render_text_description
from langchain_openai import ChatOpenAI
from langchain.tools import tool
import os
import json
from contextlib import contextmanager
import streamlit as st
import sqlite3
from dotenv import load_dotenv
import logging



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class RoomReservationAgent:

    def __init__(self):
        self.db_path = os.getenv("DB_PATH")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.chat_history = [] 
        self.initialize()

    def _process_query_result(self, query_result, from_time, to_time):
        avail_rooms = {"availableRooms": []}
        for row in query_result:
            room_data = {
                "id": row[0], 
                "name": row[1], 
                "status": row[4],
                "capacity": row[2], 
                "facilities": row[3].split(","),
                "bookingTimes": {
                    "from_time": from_time,
                    "to_time": to_time
                }, 
            }
            avail_rooms["availableRooms"].append(room_data)
        return avail_rooms

    def process(self, query):
        try:
            response = self.agent_chain.invoke({"input": query, "chat_history": self.chat_history})
        except langchain_core.exceptions.OutputParserException as e:
            print("Output parsing error:", e)
            response = "An error occurred while processing the request. Please try again later."
    
        return response

    def initialize(self):

            @tool("check_availability", return_direct=False)
            def check_availability(query: str) -> str:
                """Searches for room availability in system, input should be pipe delimited values if specific requirement like from_time(timestamp)| to_time(timestamp)| capacity(number)| list of facilities"""
                print(f"Check===================>Room {query}")
                try:
                    query_params = query.split('|')
                    from_time = query_params[0]
                    to_time = query_params[1]
                    capacity = query_params[2]
                    list_of_facilities = query_params[3].rstrip("`")
                    formatted_facilities = ",".join([f"'{facility.strip()}'" for facility in list_of_facilities.split(",")])
                    print(f"{from_time} : {to_time} : {capacity} : {formatted_facilities}")

                    sql_query = f"""SELECT 
                        r.room_id AS id, 
                        r.name, 
                        r.capacity,
                        GROUP_CONCAT(DISTINCT fm.facility_name) AS facilities,
                        CASE 
                            WHEN b.room_id IS NULL THEN 'available' 
                            ELSE 'booked' 
                        END AS status
                    FROM 
                        rooms r
                    JOIN 
                        room_facility_mappings rfm ON r.room_id = rfm.room_id
                    JOIN 
                        facility_mapping fm ON rfm.facility_id = fm.facility_id
                    LEFT JOIN 
                        bookings b ON r.room_id = b.room_id AND NOT (b.to_date < '{to_time}' OR b.from_date > '{from_time}')
                    GROUP BY 
                        r.room_id
                    HAVING 
                        SUM(CASE WHEN b.room_id IS NOT NULL THEN 1 ELSE 0 END) = 0
                        AND r.capacity >= {capacity}
                        AND SUM(CASE WHEN fm.facility_name IN ({formatted_facilities}) THEN 1 ELSE 0 END) > 0;
                    """
                    # print(sql_query)
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(sql_query)
                        rows = cursor.fetchall()
                        print(rows)
                        result = self._process_query_result(rows,from_time, to_time)
                        return f"Following room options are available : {result}"
                except Exception as e:
                    print("Error: ", e)
                    return "An error occured while checking the availability of the room"
            
            @tool("room_confirmation", return_direct=False)
            def room_confirmation(room: str) -> str:
                """Will make the room reservation,input should be pipe delimited values contains room name | room id | from_time(""%Y-%m-%dT%H:%M:%S"") | to_time("%Y-%m-%dT%H:%M:%S") """
                print(f"Reserve===================>Room {room}")
                # return "room is reserved"
                query_params = room.split('|')
                room_name = query_params[0]
                room_id = query_params[1]
                from_time = query_params[2]
                to_time = query_params[3]
                try:
                    # Execute a SQL INSERT query
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        # Check for existing bookings that overlap with the requested time slot
                        check_query = f"""
                        SELECT COUNT(*) FROM bookings
                        WHERE room_id = '{room_id}' AND NOT (to_date <= '{from_time}' OR from_date >= '{to_time}')
                        """
                        print(f"Executing query : {check_query}")
                        cursor.execute(check_query)
                        overlap_count = cursor.fetchone()[0]
                        
                        if overlap_count == 0:
                            # No overlapping bookings, proceed with reservation
                            insert_query = f"INSERT INTO bookings (from_date, to_date, room_id) VALUES ('{from_time}', '{to_time}', '{room_id}')"
                            print(f"Executing query : {insert_query}")
                            cursor.execute(insert_query)
                            #Commit changes to the database 
                            conn.commit()
                            booking_id = cursor.lastrowid
                            return f"{room_name} is reserved. Booking ID : {booking_id}"
                        else:
                            # Overlapping booking found, reservation not possible
                            return "Reservation not possible because the room is already booked at the requested slot."
                except Exception as e:
                    print("Error: ", e)
                    return "An error occured while reserving the room"

            
            @tool("cancel_confirmation", return_direct=False)
            def cancel_confirmation(booking: str) -> str:
                """Will cancel room reservation, input contains booking_id"""
                print(f"Cancel===================>Booking ID: {booking}")
                query_param = booking
                try:
                    # Execute SQL DELETE query
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        delete_query = f"DELETE FROM bookings WHERE booking_id = '{query_param}'"
                        print(f"Executing query : {delete_query}")
                        cursor.execute(delete_query)
                        #Commit changes to the database 
                        conn.commit()
                        return "Reservation cancelled"
                except Exception as e:
                    print("Error: ", e)
                    return "An error occured while cancelling the reservation"
            
        
            tools = [check_availability, room_confirmation, cancel_confirmation]
            self.memory.clear()
            llm = ChatOpenAI(model = "gpt-4-1106-preview", temperature=0)

            self.agent_chain = initialize_agent(tools,
                               llm,
                               agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                               memory=self.memory,
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
    bot = RoomReservationAgent()
    
    # chat_history = []
    # query = "I need to book a room for a client meeting next Tuesday at 11 AM for about 2 people, preferably with a whiteboard."
    # output = bot.process(query, chat_history)
    # print("=========OUTPUT==========")
    # print(output)
    # print("=========================")
    # chat_history.append(HumanMessage(content=query))
    # chat_history.append(AIMessage(content=output['output']))


    # query = "Please book the Vista Room and send me confirmatio"
    # output = bot.process(query, chat_history)
    # print("=========OUTPUT==========")
    # print(output)
    # print("=========================")
    # chat_history.append(HumanMessage(content=query))
    # chat_history.append(AIMessage(content=output['output']))

    # query = "What's my last booking ID? What rooom was booked?"
    # output = bot.process(query, chat_history)
    # print("=========OUTPUT==========")
    # print(output)
    # print("=========================")
    # chat_history.append(HumanMessage(content=query))
    # chat_history.append(AIMessage(content=output['output']))

    # query = "Cancel my reservation with booking id is 17"
    # output = bot.process(query, chat_history)
    # print("=========OUTPUT==========")
    # print(output)
    # print("=========================")
    # chat_history.append(HumanMessage(content=query))
    # chat_history.append(AIMessage(content=output['output']))

    # os._exit()
    # Persistent state to store chat history\
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

    
    #Close SQLite connection when done 
    #bot.conn.close()