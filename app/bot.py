import os
import json
import asyncio
import datetime
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph,END
from classStructs import MDdata,Mail,CalendarList,Transportation,CalendarResponse,MailList,LocationCoordinates,Weather,BooleanResponse,WeatherInfo
from my_mcp import mcp_config

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from typing import Dict,TypedDict,List
from templates.prompts import calendar_prompt_format,calendar_prompt2,transportation_prompt,email_prompt,email_format_prompt,weather_prompt,transport_response_checker

from jinja2 import Environment, FileSystemLoader, Template
class DayAgentState(TypedDict):
    agent: "DayAgent"

class DayAgent():
    def __init__(self):
        self.data_collector = DataCollector()
        self.content_processor = ContentProcessor()
        self.pdf_gen = PDFGenerator()
        self.graph =self._build_graph()


    def _build_graph(self)->StateGraph:
        """ This method builds the langgraph Graph object
        
        """
        print("\nMade it into method: DayAgent._build_graph!!\n")

        graph = StateGraph(DayAgentState)
        # Add nodes

        graph.add_node("Load config node",self.data_collector.load_config_node)
        graph.add_node("Calendar_node",self.data_collector.check_calender)


        graph.add_node("transportation_node",self.data_collector.transportation_node)
        graph.add_node("mail_node",self.data_collector.mail_node)
        graph.add_node("Location->GeoCord_node",self.data_collector.locToGeocode)
        graph.add_node("weather_node",self.data_collector.weather_node)
        graph.add_node("saving_json_node",self.data_collector.saveConf)
        graph.add_node("generate_md",self.content_processor.generate_md)

        
        
        # Edges
        # graph.set_entry_point("Load config node")
        # graph.add_edge("Load config node","Calendar_node")
        # graph.add_conditional_edges("Calendar_node",self.data_collector.events_exist,{True:"transportation_node",False:"mail_node"})
        # graph.add_edge("transportation_node","mail_node")
        # 
        # graph.add_edge("mail_node","Location->GeoCord_node")
        # graph.add_edge("Location->GeoCord_node","weather_node")
        # graph.add_edge("weather_node","saving_json_node")
        # graph.add_edge("saving_json_node",END)



        graph.set_entry_point("Load config node")
        graph.add_edge("Load config node","generate_md")
        graph.add_edge("generate_md",END)





        memory = MemorySaver()

        return graph.compile(checkpointer=memory)                    # Add memory here!
    

    def run(self):
        data = self._set_entry_data()
        pass

    def _set_entry_data(self)-> MDdata:
        """ This method sets the init config """
        path = os.getcwd
        if "/app" not in path:
            path = path + "/app"
        path = path + "/user_conf/config.json"
        with open(path,"r") as f:
            user_conf = json.load(f)
        print(user_conf)
            
        return (MDdata())

class DataCollector:
    """
    This class gathers all data collection and graph method declaration
    """
    def __init__(self):
        self.llm_model = None
        self.config = None              # Maybe strange Init value, look at later 
        self.llmConfig = None
        self.data = None

    async def setLLM(self,new_model=False,response_format=None):
        """
        Method that creates LLM models, three different types:
            1. self.llm_model(init)
            2. standalone model
            3. respone formatted model
        """
        
        print("\nMade it into method: DataCollector.setLLM\n")

        with open ("mcp_config.json",'r') as f:
            mcp_config = json.load(f)

        client = MultiServerMCPClient(connections=mcp_config['mcpServers'])
        tools  = await client.get_tools()
        memory = MemorySaver()
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash",temperature=0)
        if not new_model:
            self.llm_model = create_react_agent(model, tools,checkpointer=memory)
        else:
            if response_format== None:
                return create_react_agent(model, tools,checkpointer=memory)
            else:
                return create_react_agent(model, tools,response_format=response_format,checkpointer=memory)
        


   
    
    def load_config_node(self,state: DayAgentState)->DayAgentState:
        """ 
            This method loads and sets the config
        
        """
        
        print(" \n\nMade it into method: DataCollector.load_config_node\n")

        # Path correction
        dirname = os.path.dirname(__file__)
        if "/app" not in dirname:
            dirname = dirname + "/app"
        
        filename = os.path.join(dirname, "user_conf","config.json")
        
        # Open json
        with open(filename,"r") as f:
            conf = json.load(f)
        
        self.config = self.populateData(conf)
        self.llmConfig = {"configurable": {"thread_id": "1"}}
        
        return state

    def populateData(self,user_dict: Dict)->MDdata:
        """ This method populates the data in the MDdata class"""
        dataClass = self.initClass()
        dataKeys = dataClass.keys()

        for key in user_dict.keys():
            if key in dataKeys:
                dataClass[key]=user_dict[key]
        return dataClass



    def initClass(self)->MDdata:        # Always add Classes here when implementing new!
        print(" \nMade it into method: DataCollector.initClass\n")
        
        return MDdata(name="",
                      location="",
                      work_location=[],
                      home_location=[],
                      dentist_location=[],
                      calendar_events =[],
                      transportation_list=[],
                      new_email= [],
                      weather=[]
                      )



    
    async def check_calender(self,state: DayAgentState)->DayAgentState:
        """
        This method checks the calendar for today's events and lists them
        
        """
        print(" \nMade it into method: DataCollector.check_calender\n")
        
        calendar_model = await self.setLLM(new_model=True,response_format=CalendarList)
        
        
        agent_response = await self.llm_model.ainvoke({"messages": [HumanMessage(content=calendar_prompt2)]},config=self.llmConfig)
        temp= agent_response['messages'][-1].content
        jsonReturn = json.loads(temp[7:-3])                 # Change to regex!
        calendar_prompt_format_populated = calendar_prompt_format.format(data=jsonReturn)

        agent_response = await calendar_model.ainvoke({"messages": [HumanMessage(content=calendar_prompt_format_populated)]},config=self.llmConfig)
        if agent_response["structured_response"].events != []:
            self.config["calendar_events"] = agent_response["structured_response"].events
        
        # print(self.config["calendar_events"])
        # print(agent_response["structured_response"].events)

        return state    
        


    def events_exist(self,state:DayAgentState)->bool:
        """
        This method checks if there exist any events for the day, if it doesnt, it will return false
        
        """
        print(" \nMade it into method: DataCollector.events_exist\n")

        if self.config["calendar_events"] == []:
            return False

        return True


    async def transportation_node(self,state: DayAgentState):

        """

        This node will check the home_location, and what calendar events are planned today,
        to look for how transportation should be done to get to said location.


        """
        
        """
            Todo:
                - Check config for location of home,work and dentist
                - Check schedule to find next location    
    
        
        
        """


        print(" \nMade it into method: DataCollector.transportation_node\n")


        # List generation for transportation

        home_add = f"{self.config['home_location'][0]['address']}, {self.config['home_location'][0]['city']}"
        addresses = [location.location for location in self.config["calendar_events"]]
        
        addresses.insert(0,home_add)
        addresses.append(home_add)


        # LLM call and transportation query
        response_model = await self.setLLM(new_model=True,response_format=BooleanResponse)
        

        for adress in range(len(addresses)):
            if adress + 1 != len(addresses):
                transportation_prompt_formatted = transportation_prompt.format(start=addresses[adress],end=addresses[adress+1])

                agent_response1 = await self.llm_model.ainvoke({"messages": [HumanMessage(content=transportation_prompt_formatted)]},config=self.llmConfig)
                
                checker_format = transport_response_checker.format(answer=agent_response1['messages'][-1].content)
                agent_response2 = await response_model.ainvoke({"messages": [HumanMessage(content=checker_format)]},config=self.llmConfig)
                if agent_response2['structured_response'].is_valid:
                    self.config["transportation_list"].append(Transportation(info=agent_response1['messages'][-1].content))



    async def mail_node(self,state:DayAgentState):
        """
        This method checks the Gmail tool and gathers new daily emails.
        """


        print(" \nMade it into method: DataCollector.mail_node\n")
        
        # formatting

        msg_formated = email_prompt.format(location=self.config["location"])
        
        # New LLM for structured response
        response_formatted_model = await self.setLLM(new_model=True,response_format=MailList)

        # Model call
        agent_response = await self.llm_model.ainvoke({"messages": [HumanMessage(content=msg_formated)]},config=self.llmConfig)
        
        # formatting
        
        formatted_email_format_prompt = email_format_prompt.format(email_data=agent_response['messages'][-1].content)
        
        # Model call
        formatted_agent_response = await response_formatted_model.ainvoke({"messages": [HumanMessage(content=formatted_email_format_prompt)]},config=self.llmConfig)
        # print(f"formatted msg: {msg_formated}\n")
        # print(f"First response: {agent_response['messages'][-1].content}")
        # print(f"Answer: {formatted_agent_response['structured_response']}\n")

        # Setting new emails
        self.config["new_email"] = formatted_agent_response["structured_response"]
        # print(self.config)


    async def locToGeocode(self,state:DayAgentState):
        """
        This node is used to find home_location latitude and longitude.

        After this method, in beta we should check if its valid(Future edition)

        """

        # self.config = {'name': 'Oden', 'location': 'Stockholm', 'work_location': [{'address': 'Råstavägen 3', 'city': 'Solna', 'postal code': '169 54'}], 'home_location': [{'address': 'Kungsholms Strand 159', 'city': 'Stockholm', 'postal code': '112 48'}], 'dentist_location': [{'address': None, 'city': None, 'postal code': None}], 'calendar_events': CalendarList(events=[CalendarResponse(Event_id='_8gpk4ca188s46ba48p238b9k6gp3cb9o8gpk2ba46l1jadpk8h2k6e236c', summary='Mattias Jobba', start='2025-10-02T10:15:00+02:00', end='2025-10-02T11:15:00+02:00', view='', location='Råstavägen 3\n169 54 Solna, Sverige'), CalendarResponse(Event_id='5l1uraj9fdhvn0n8q4717mi75c', summary='T1 Calendar', start='2025-10-02T16:30:00+02:00', end='2025-10-02T17:30:00+02:00', view='', location='Stockholm, Sverige'), CalendarResponse(Event_id='4htgrk8os48abtpkqfbkf6v7o8', summary='t2 calendar', start='2025-10-02T17:00:00+02:00', end='2025-10-02T19:00:00+02:00', view='', location='Uddevalla, Sverige'), CalendarResponse(Event_id='it6p62uuqmsjopjci0vdb3sor0', summary='The Sacred Session at Sacred Sauna', start='2025-10-02T18:30:00+02:00', end='2025-10-02T19:30:00+02:00', view='', location='Sacred Sauna')]), 'transportation_list': [Transportation(info='From: Kungsholms Strand 159, Stockholm\nTo: Råstavägen 3, 169 54 Solna, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 27 minutes from now\n- Total Travel Duration: 27 minutes\n- Transit Lines/Routes:\n  - Walk to Stadshagen (12 minutes)\n  - Subway towards Akalla (6 minutes)\n  - Walk to Råstavägen 3, 169 54 Solna, Sweden (9 minutes)'), Transportation(info='From: Råstavägen 3, 169 54 Solna, Sverige\nTo: Stockholm, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 20 minutes from now\n- Total Travel Duration: 20 minutes\n- Transit Lines/Routes:\n  - Walk to Östervägen (4 minutes)\n  - Bus towards Solna centrum (7 minutes)\n  - Walk to Solna centrum (1 minute)\n  - Bus towards Blackebergs gård (5 minutes)'), Transportation(info='From: Stockholm, Sverige\nTo: Uddevalla, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 4 hours 13 minutes from now\n- Total Travel Duration: 4 hours 13 minutes\n- Transit Lines/Routes:\n  - High speed train towards Göteborg Centralstation (2 hours 42 mins)\n  - Train towards Uddevalla Centralstation (1 hour 22 mins)'), Transportation(info="From: Uddevalla, Sverige\nTo: Sacred Sauna\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 1 day 3 hours from now\n- Total Travel Duration: 1 day 3 hours\n- Transit Lines/Routes:\n  - Bus towards Göteborg Nils Ericsonterminal (1 hour 15 mins)\n  - Walk to Gothenburg Central Station (2 mins)\n  - High speed train towards Malmö Centralstation (2 hours 30 mins)\n  - Walk to Malmo Norra Vallgatan (3 mins)\n  - Bus towards Paris Bercy Central Bus Station (11 hours 20 mins)\n  - Walk to Arnhem Central (1 min)\n  - Train towards Den Helder (37 mins)\n  - Walk to Utrecht Centraal (1 min)\n  - Train towards Dordrecht (31 mins)\n  - High speed train towards Paris-Nord (1 hour 39 mins)\n  - Walk to Brussels Midi Train Station (2 mins)\n  - High speed train towards London St Pancras Int'l (2 hours 6 mins)\n  - Walk to King's Cross St. Pancras (3 mins)\n  - Subway towards Hammersmith (10 mins)\n  - Walk to Paddington (2 mins)\n  - Train towards Penzance (1 hour 41 mins)\n  - Walk to Taunton Station South Side (2 mins)\n  - Bus towards Langley Corner, Bus (33 mins)\n  - Walk to Winkley House Studio, Fore St, Milverton, Taunton TA4 1JU, UK (4 mins)")], 'new_email': MailList(mails=[Mail(subject='Work', sender='Oden Allen <oden.allen@gmail.com>', summary='Work. No preview available.'), Mail(subject='💡🧠 What makes you, you?', sender='Lumosity <newsletter@notifications.lumosity.com>', summary='💡🧠 What makes you, you? No preview available.'), Mail(subject='Ett förtvivlat fint erbjudande – 1 månad för 9 kr 📚', sender='BookBeat <team@news.bookbeat.com>', summary='Ett förtvivlat fint erbjudande – 1 månad för 9 kr 📚. No preview available.'), Mail(subject='“software engineer”: Generate - AI Backend Developer and more', sender='LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>', summary='“software engineer”: Generate - AI Backend Developer and more. No preview available.'), Mail(subject='Deploja AB: 4 nya jobb matchar din profil', sender='Deploja AB <no-reply@deplojaab.teamtailor-mail.com>', summary='Deploja AB: 4 nya jobb matchar din profil. No preview available.'), Mail(subject='“software engineer”: Solita - AI Developer – Stockholm and more', sender='LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>', summary='“software engineer”: Solita - AI Developer – Stockholm and more. No preview available.'), Mail(subject='Ditt paket är på väg från Jollyroom.se', sender='"Jollyroom.se" <no-reply@jollyroom.se>', summary='Ditt paket är på väg från Jollyroom.se. No preview available.'), Mail(subject='Påminnelse: Obetald elfaktura från Greenely', sender='No reply <noreply@delivery.payex.com>', summary='Påminnelse: Obetald elfaktura från Greenely. No preview available.'), Mail(subject='Veckans erbjudanden i din butik', sender='Coop <info@e.coop.se>', summary='Veckans erbjudanden i din butik. No preview available.'), Mail(subject='1 LAST Chance To Receive 2 Rewards After Your Getaway 🏖️', sender='Hilton Grand Vacations <hgv@travel.hiltongrandvacations.com>', summary='1 LAST Chance To Receive 2 Rewards After Your Getaway 🏖️. No preview available.')])}
        # print(" \nMade it into method: DataCollector.locToGeocode_node\n")
        # print(f"Home Location: \n {self.config['home_location']}")
        
        msg= """I would like for you to give me a geocode from a location.\n
        Address: {address}, {postal_code} in {city}
                
                
                """
        msg_format=msg.format(address=self.config['home_location'][0]['address'],postal_code=self.config['home_location'][0]['postal code'],city = self.config['home_location'][0]['city'])
        print(msg_format)
        response_model = await self.setLLM(new_model=True,response_format=LocationCoordinates)
        formatted_agent_response = await response_model.ainvoke({"messages": [HumanMessage(content=msg_format)]},config=self.llmConfig)

        print(f"conf: {self.config['home_location'][0]}")

        if formatted_agent_response["structured_response"].latitude != float(0) and formatted_agent_response["structured_response"].longitude!=float(0):
            self.config['home_location'][0]['latitude'] = formatted_agent_response["structured_response"].latitude
            self.config['home_location'][0]['longitude'] = formatted_agent_response["structured_response"].longitude
        print(f"conf: {self.config['home_location'][0]}")
        return state

    async def weather_node(self,state:DayAgentState):
        """
        This node check checks the Weather report for today. It return hourly Temperature(celcius) and Percipitation information

        """
        print(" \nMade it into method: DataCollector.weather_node\n")


                # TO be removed later

        self.config = {'name': 'Oden', 'location': 'Stockholm', 'work_location': [{'address': 'Råstavägen 3', 'city': 'Solna', 'postal code': '169 54'}], 'home_location': [{'address': 'Kungsholms Strand 159', 'city': 'Stockholm', 'postal code': '112 48'}], 'dentist_location': [{'address': None, 'city': None, 'postal code': None}], 'calendar_events': CalendarList(events=[CalendarResponse(Event_id='_8gpk4ca188s46ba48p238b9k6gp3cb9o8gpk2ba46l1jadpk8h2k6e236c', summary='Mattias Jobba', start='2025-10-02T10:15:00+02:00', end='2025-10-02T11:15:00+02:00', view='', location='Råstavägen 3\n169 54 Solna, Sverige'), CalendarResponse(Event_id='5l1uraj9fdhvn0n8q4717mi75c', summary='T1 Calendar', start='2025-10-02T16:30:00+02:00', end='2025-10-02T17:30:00+02:00', view='', location='Stockholm, Sverige'), CalendarResponse(Event_id='4htgrk8os48abtpkqfbkf6v7o8', summary='t2 calendar', start='2025-10-02T17:00:00+02:00', end='2025-10-02T19:00:00+02:00', view='', location='Uddevalla, Sverige'), CalendarResponse(Event_id='it6p62uuqmsjopjci0vdb3sor0', summary='The Sacred Session at Sacred Sauna', start='2025-10-02T18:30:00+02:00', end='2025-10-02T19:30:00+02:00', view='', location='Sacred Sauna')]), 'transportation_list': [Transportation(info='From: Kungsholms Strand 159, Stockholm\nTo: Råstavägen 3, 169 54 Solna, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 27 minutes from now\n- Total Travel Duration: 27 minutes\n- Transit Lines/Routes:\n  - Walk to Stadshagen (12 minutes)\n  - Subway towards Akalla (6 minutes)\n  - Walk to Råstavägen 3, 169 54 Solna, Sweden (9 minutes)'), Transportation(info='From: Råstavägen 3, 169 54 Solna, Sverige\nTo: Stockholm, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 20 minutes from now\n- Total Travel Duration: 20 minutes\n- Transit Lines/Routes:\n  - Walk to Östervägen (4 minutes)\n  - Bus towards Solna centrum (7 minutes)\n  - Walk to Solna centrum (1 minute)\n  - Bus towards Blackebergs gård (5 minutes)'), Transportation(info='From: Stockholm, Sverige\nTo: Uddevalla, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 4 hours 13 minutes from now\n- Total Travel Duration: 4 hours 13 minutes\n- Transit Lines/Routes:\n  - High speed train towards Göteborg Centralstation (2 hours 42 mins)\n  - Train towards Uddevalla Centralstation (1 hour 22 mins)'), Transportation(info="From: Uddevalla, Sverige\nTo: Sacred Sauna\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 1 day 3 hours from now\n- Total Travel Duration: 1 day 3 hours\n- Transit Lines/Routes:\n  - Bus towards Göteborg Nils Ericsonterminal (1 hour 15 mins)\n  - Walk to Gothenburg Central Station (2 mins)\n  - High speed train towards Malmö Centralstation (2 hours 30 mins)\n  - Walk to Malmo Norra Vallgatan (3 mins)\n  - Bus towards Paris Bercy Central Bus Station (11 hours 20 mins)\n  - Walk to Arnhem Central (1 min)\n  - Train towards Den Helder (37 mins)\n  - Walk to Utrecht Centraal (1 min)\n  - Train towards Dordrecht (31 mins)\n  - High speed train towards Paris-Nord (1 hour 39 mins)\n  - Walk to Brussels Midi Train Station (2 mins)\n  - High speed train towards London St Pancras Int'l (2 hours 6 mins)\n  - Walk to King's Cross St. Pancras (3 mins)\n  - Subway towards Hammersmith (10 mins)\n  - Walk to Paddington (2 mins)\n  - Train towards Penzance (1 hour 41 mins)\n  - Walk to Taunton Station South Side (2 mins)\n  - Bus towards Langley Corner, Bus (33 mins)\n  - Walk to Winkley House Studio, Fore St, Milverton, Taunton TA4 1JU, UK (4 mins)")], 'new_email': MailList(mails=[Mail(subject='Work', sender='Oden Allen <oden.allen@gmail.com>', summary='Work. No preview available.'), Mail(subject='💡🧠 What makes you, you?', sender='Lumosity <newsletter@notifications.lumosity.com>', summary='💡🧠 What makes you, you? No preview available.'), Mail(subject='Ett förtvivlat fint erbjudande – 1 månad för 9 kr 📚', sender='BookBeat <team@news.bookbeat.com>', summary='Ett förtvivlat fint erbjudande – 1 månad för 9 kr 📚. No preview available.'), Mail(subject='“software engineer”: Generate - AI Backend Developer and more', sender='LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>', summary='“software engineer”: Generate - AI Backend Developer and more. No preview available.'), Mail(subject='Deploja AB: 4 nya jobb matchar din profil', sender='Deploja AB <no-reply@deplojaab.teamtailor-mail.com>', summary='Deploja AB: 4 nya jobb matchar din profil. No preview available.'), Mail(subject='“software engineer”: Solita - AI Developer – Stockholm and more', sender='LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>', summary='“software engineer”: Solita - AI Developer – Stockholm and more. No preview available.'), Mail(subject='Ditt paket är på väg från Jollyroom.se', sender='"Jollyroom.se" <no-reply@jollyroom.se>', summary='Ditt paket är på väg från Jollyroom.se. No preview available.'), Mail(subject='Påminnelse: Obetald elfaktura från Greenely', sender='No reply <noreply@delivery.payex.com>', summary='Påminnelse: Obetald elfaktura från Greenely. No preview available.'), Mail(subject='Veckans erbjudanden i din butik', sender='Coop <info@e.coop.se>', summary='Veckans erbjudanden i din butik. No preview available.'), Mail(subject='1 LAST Chance To Receive 2 Rewards After Your Getaway 🏖️', sender='Hilton Grand Vacations <hgv@travel.hiltongrandvacations.com>', summary='1 LAST Chance To Receive 2 Rewards After Your Getaway 🏖️. No preview available.')])}

        self.config['home_location'][0] = {'address': 'Kungsholms Strand 159', 'city': 'Stockholm', 'postal code': '112 48', 'latitude': 59.3382069, 'longitude': 18.0258636}


                # Populating Docstring prompt

        weather_prompt_formatted = weather_prompt.format(timezone=self.config['location'],latitude=self.config['home_location'][0]['latitude'],longitude=self.config['home_location'][0]['longitude'])
        
                # formatted response model
        response_model = await self.setLLM(new_model=True,response_format=Weather)
        
                # Model call
        agent_response = await response_model.ainvoke({"messages": [HumanMessage(content=weather_prompt_formatted)]},config=self.llmConfig)
        
                # Config assignment
        
        self.config["weather"] = agent_response["structured_response"].hourly_weather
        print(f"\nweather return: {agent_response['structured_response'].hourly_weather}\n")
        return state
    

    def saveConf(self,state: DayAgentState):
        """
        Saves config to work on MD maker.
        
        """
        print(" \nMade it into method: DataCollector.saveConf\n")
        self.config = {'name': 'Oden', 'location': 'Stockholm', 'work_location': [{'address': 'Råstavägen 3', 'city': 'Solna', 'postal code': '169 54'}], 'home_location': [{'address': 'Kungsholms Strand 159', 'city': 'Stockholm', 'postal code': '112 48', 'latitude': 59.3382069, 'longitude': 18.0258636}], 'dentist_location': [{'address': None, 'city': None, 'postal code': None}], 'calendar_events': CalendarList(events=[CalendarResponse(Event_id='_8gpk4ca188s46ba48p238b9k6gp3cb9o8gpk2ba46l1jadpk8h2k6e236c', summary='Mattias Jobba', start='2025-10-02T10:15:00+02:00', end='2025-10-02T11:15:00+02:00', view='', location='Råstavägen 3\n169 54 Solna, Sverige'), CalendarResponse(Event_id='5l1uraj9fdhvn0n8q4717mi75c', summary='T1 Calendar', start='2025-10-02T16:30:00+02:00', end='2025-10-02T17:30:00+02:00', view='', location='Stockholm, Sverige'), CalendarResponse(Event_id='4htgrk8os48abtpkqfbkf6v7o8', summary='t2 calendar', start='2025-10-02T17:00:00+02:00', end='2025-10-02T19:00:00+02:00', view='', location='Uddevalla, Sverige'), CalendarResponse(Event_id='it6p62uuqmsjopjci0vdb3sor0', summary='The Sacred Session at Sacred Sauna', start='2025-10-02T18:30:00+02:00', end='2025-10-02T19:30:00+02:00', view='', location='Sacred Sauna')]), 'transportation_list': [Transportation(info='From: Kungsholms Strand 159, Stockholm\nTo: Råstavägen 3, 169 54 Solna, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 27 minutes from now\n- Total Travel Duration: 27 minutes\n- Transit Lines/Routes:\n  - Walk to Stadshagen (12 minutes)\n  - Subway towards Akalla (6 minutes)\n  - Walk to Råstavägen 3, 169 54 Solna, Sweden (9 minutes)'), Transportation(info='From: Råstavägen 3, 169 54 Solna, Sverige\nTo: Stockholm, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 20 minutes from now\n- Total Travel Duration: 20 minutes\n- Transit Lines/Routes:\n  - Walk to Östervägen (4 minutes)\n  - Bus towards Solna centrum (7 minutes)\n  - Walk to Solna centrum (1 minute)\n  - Bus towards Blackebergs gård (5 minutes)'), Transportation(info='From: Stockholm, Sverige\nTo: Uddevalla, Sverige\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 4 hours 13 minutes from now\n- Total Travel Duration: 4 hours 13 minutes\n- Transit Lines/Routes:\n  - High speed train towards Göteborg Centralstation (2 hours 42 mins)\n  - Train towards Uddevalla Centralstation (1 hour 22 mins)'), Transportation(info="From: Uddevalla, Sverige\nTo: Sacred Sauna\nMode: Public Transportation\n\nRoute 1:\n- Departure Time: Now\n- Arrival Time: 1 day 3 hours from now\n- Total Travel Duration: 1 day 3 hours\n- Transit Lines/Routes:\n  - Bus towards Göteborg Nils Ericsonterminal (1 hour 15 mins)\n  - Walk to Gothenburg Central Station (2 mins)\n  - High speed train towards Malmö Centralstation (2 hours 30 mins)\n  - Walk to Malmo Norra Vallgatan (3 mins)\n  - Bus towards Paris Bercy Central Bus Station (11 hours 20 mins)\n  - Walk to Arnhem Central (1 min)\n  - Train towards Den Helder (37 mins)\n  - Walk to Utrecht Centraal (1 min)\n  - Train towards Dordrecht (31 mins)\n  - High speed train towards Paris-Nord (1 hour 39 mins)\n  - Walk to Brussels Midi Train Station (2 mins)\n  - High speed train towards London St Pancras Int'l (2 hours 6 mins)\n  - Walk to King's Cross St. Pancras (3 mins)\n  - Subway towards Hammersmith (10 mins)\n  - Walk to Paddington (2 mins)\n  - Train towards Penzance (1 hour 41 mins)\n  - Walk to Taunton Station South Side (2 mins)\n  - Bus towards Langley Corner, Bus (33 mins)\n  - Walk to Winkley House Studio, Fore St, Milverton, Taunton TA4 1JU, UK (4 mins)")], 'new_email': MailList(mails=[Mail(subject='Work', sender='Oden Allen <oden.allen@gmail.com>', summary='Work. No preview available.'), Mail(subject='💡🧠 What makes you, you?', sender='Lumosity <newsletter@notifications.lumosity.com>', summary='💡🧠 What makes you, you? No preview available.'), Mail(subject='Ett förtvivlat fint erbjudande – 1 månad för 9 kr 📚', sender='BookBeat <team@news.bookbeat.com>', summary='Ett förtvivlat fint erbjudande – 1 månad för 9 kr 📚. No preview available.'), Mail(subject='“software engineer”: Generate - AI Backend Developer and more', sender='LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>', summary='“software engineer”: Generate - AI Backend Developer and more. No preview available.'), Mail(subject='Deploja AB: 4 nya jobb matchar din profil', sender='Deploja AB <no-reply@deplojaab.teamtailor-mail.com>', summary='Deploja AB: 4 nya jobb matchar din profil. No preview available.'), Mail(subject='“software engineer”: Solita - AI Developer – Stockholm and more', sender='LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>', summary='“software engineer”: Solita - AI Developer – Stockholm and more. No preview available.'), Mail(subject='Ditt paket är på väg från Jollyroom.se', sender='"Jollyroom.se" <no-reply@jollyroom.se>', summary='Ditt paket är på väg från Jollyroom.se. No preview available.'), Mail(subject='Påminnelse: Obetald elfaktura från Greenely', sender='No reply <noreply@delivery.payex.com>', summary='Påminnelse: Obetald elfaktura från Greenely. No preview available.'), Mail(subject='Veckans erbjudanden i din butik', sender='Coop <info@e.coop.se>', summary='Veckans erbjudanden i din butik. No preview available.'), Mail(subject='1 LAST Chance To Receive 2 Rewards After Your Getaway 🏖️', sender='Hilton Grand Vacations <hgv@travel.hiltongrandvacations.com>', summary='1 LAST Chance To Receive 2 Rewards After Your Getaway 🏖️. No preview available.')]), 'weather': [WeatherInfo(hour='12:00', temperature='13.35', precipitation='0.02'), WeatherInfo(hour='13:00', temperature='14.05', precipitation='0.05'), WeatherInfo(hour='14:00', temperature='14.55', precipitation='0.07'), WeatherInfo(hour='15:00', temperature='14.82', precipitation='0.06'), WeatherInfo(hour='16:00', temperature='14.89', precipitation='0.05'), WeatherInfo(hour='17:00', temperature='14.62', precipitation='0.03'), WeatherInfo(hour='18:00', temperature='13.79', precipitation='0.02'), WeatherInfo(hour='19:00', temperature='12.62', precipitation='0.01'), WeatherInfo(hour='20:00', temperature='11.59', precipitation='0.00'), WeatherInfo(hour='21:00', temperature='10.88', precipitation='0.00'), WeatherInfo(hour='22:00', temperature='10.31', precipitation='0.00'), WeatherInfo(hour='23:00', temperature='9.81', precipitation='0.00')]}
        dirname = os.path.dirname(__file__)
        print(dirname)
        
        if "/app" in dirname:
            dirname = dirname.replace("/app","")


        config_serializable = {
            "name": self.config["name"],
            "location": self.config["location"],
            "work_location": self.config["work_location"],
            "home_location": self.config["home_location"],
            "dentist_location": self.config["dentist_location"],
            "calendar_events": [event.model_dump() for event in self.config["calendar_events"].events],
            "transportation_list": [t.model_dump() for t in self.config["transportation_list"]],
            "new_email": [mail.model_dump() for mail in self.config["new_email"].mails],
            "weather": [w.model_dump() for w in self.config["weather"]]
        }

        savePath =os.path.join(dirname,"result","results.json") 
        print(savePath)
        with open(savePath, 'w') as f:
            json.dump(config_serializable, f, indent=2)





class ContentProcessor:
    """ This class  renders MD jinja2 template"""
    

    def __init__(self):
        self.path = os.path.dirname(__file__)


    def generate_md(self,state: DayAgentState):
        """
        This method populates the markdown template with the data from the results.json 
        file generated earlier in the graph
        
        """
        print(" \nMade it into method: content_processor.generate_md\n")

                # Load json data
        keysList = ["calendar_events","transportation_list","new_email","weather"]
        data = self.loadfile(keysList)
        data["date"] = datetime.date.today().isoformat()


        calendar_with_transport = []
        for i, event in enumerate(data['calendar_events']):
            event_data = event.copy()
            # Add corresponding transportation if it exists
            if i < len(data['transportation_list']):
                event_data['transportation'] = data['transportation_list'][i]['info']
            else:
                event_data['transportation'] = 'No transportation info available'
            calendar_with_transport.append(event_data)


        template_data = {
        'date': data['date'],
        'calendar_events': calendar_with_transport,
        'weather': data['weather'],
        'new_email': data['new_email']
        }


        template = self.load_template_from_file()
        save_path = os.path.join(self.path,"result","generatedMD.md")
        print(save_path)
        
        with open(save_path, 'w') as f:
            f.write(template.render(**template_data))

        


    def load_template_from_file(self):
        """ This method loads the template that will be populated"""
        print(" \nMade it into method: content_processor.load_template_from_file\n")
        template_dir = os.path.dirname("templates/email-template.md")
        template_name = os.path.basename("templates/email-template.md")
        print(template_dir)
        print(template_name)
        env = Environment(loader=FileSystemLoader(template_dir))
        return env.get_template(template_name)



    def loadfile(self,keys:List[str] = None)->json:
        """ This method loads the result data and returns json format"""
        print(" \nMade it into method: content_processor.loadfile\n")
        
        if "/app" in self.path:
            self.path = self.path.replace("/app","")
        
        path = os.path.join(self.path,"result","results.json")

        
        with open(path, 'r') as f:
            data = json.load(f)
    
        if keys:
            return {key: data[key] for key in keys if key in data}
    
        return data





class PDFGenerator:
    
    """
    UNKNOWN
    This Class generates the PDF(IF We choose to have this format! )
    UNKNOWN
    """
    
    pass



async def run(obj: DayAgent):
    print(" \nMade it into method: Run\n")

    conf = {"configurable": {"thread_id": "1"}}
    inputs = {"messages": [HumanMessage(content="We trying this!")]}
    agent_response = await obj.graph.ainvoke(inputs,conf)



    
async def main():
    t2 = DayAgent()
    await t2.data_collector.setLLM()
   
    
    user_input = "show me the raw output you get when you query about the email with message id: 1995d921db9f08b9'. Give it to me in the exakt form the MCP tool gives you. If you recieve a error when trying to access your tools, please let me know."
    while True:
        if user_input in ["quit", "exit","q"]:
            break
        await run(t2)

        exit()

    


if __name__ == "__main__":
    
    asyncio.run(main())
