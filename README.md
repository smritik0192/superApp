# SuperApp README 

## Introduction

Welcome to the SuperApp repository! This project is designed to provide a comprehensive solution for managing various reservations through an intuitive interface. Currently, the repository hosts two main applications: a parking lot reservation agent and a room reservation system, both powered by Streamlit and designed to leverage large language models for efficient and user-friendly interactions.

## Installation

Before you can run the applications, ensure you have the necessary prerequisites installed on your system. This section guides you through the setup process.

### Prerequisites

- Python 3.6 or newer
- pip (Python package installer)

### Setting Up Your Environment

1. **Clone the Repository**

   First, clone the SuperApp repository to your local machine using Git:

   ```
   git clone https://github.com/smritik0192/superApp.git
   cd superApp
   ```

2. **Install Dependencies**

   Install the required Python packages using pip:

   ```
   pip install -r requirements.txt
   ```

   This command will install all the dependencies listed in the `requirements.txt` file, including Streamlit.

## How to Use

### Running the Applications

This repository includes two main applications: a parking lot reservation agent and a room reservation system. Here's how to run each of them:

- **Parking Lot Reservation Agent**

  Navigate to the `chatbot_llm` directory and run the following command:

  ```
  streamlit run parking_lot_reservation_agent.py
  ```

- **Room Reservation System (Version 2)**

  Similarly, to run the room reservation system, use:

  ```
  streamlit run room_reservation_agentV2.py
  ```

### Interacting with the Applications

After running the desired application, Streamlit will start a server and open a web browser window automatically. Use the application to interact with the Chatbot.
