import os
import json
import asyncio
import datetime
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph,END
from classStructs import MDdata,CalendarList,Transportation,MailList,LocationCoordinates,Weather,BooleanResponse,WeatherInfo
from my_mcp import mcp_config

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from typing import Dict,TypedDict,List
from templates.prompts import calendar_prompt_format,calendar_prompt2,transportation_prompt,email_prompt,email_format_prompt,weather_prompt,transport_response_checker,locToGeo_msg

from jinja2 import Environment, FileSystemLoader, Template
class DayAgentState(TypedDict):
    agent: "DayAgent"

class DayAgent():
    def __init__(self):
        self.data_collector = DataCollector()
        self.content_processor = ContentProcessor()
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
        graph.set_entry_point("Load config node")
        graph.add_edge("Load config node","Calendar_node")
        graph.add_conditional_edges("Calendar_node",self.data_collector.events_exist,{True:"transportation_node",False:"mail_node"})
        graph.add_edge("transportation_node","mail_node")
        
        graph.add_edge("mail_node","Location->GeoCord_node")
        graph.add_edge("Location->GeoCord_node","weather_node")
        graph.add_edge("weather_node","saving_json_node")
        graph.add_edge("saving_json_node","generate_md")
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
        
        # Setting new emails
        self.config["new_email"] = formatted_agent_response["structured_response"]


    async def locToGeocode(self,state:DayAgentState):
        """
        This node is used to find home_location latitude and longitude.

        After this method, in beta we should check if its valid(Future edition)

        """

            # Format
        
        msg_format=locToGeo_msg.format(address=self.config['home_location'][0]['address'],postal_code=self.config['home_location'][0]['postal code'],city = self.config['home_location'][0]['city'])
        
            # new model generation
        response_model = await self.setLLM(new_model=True,response_format=LocationCoordinates)
            
            # LLM call
        formatted_agent_response = await response_model.ainvoke({"messages": [HumanMessage(content=msg_format)]},config=self.llmConfig)


            # Value checker
        if formatted_agent_response["structured_response"].latitude != float(0) and formatted_agent_response["structured_response"].longitude!=float(0):
            self.config['home_location'][0]['latitude'] = formatted_agent_response["structured_response"].latitude
            self.config['home_location'][0]['longitude'] = formatted_agent_response["structured_response"].longitude



        return state

    async def weather_node(self,state:DayAgentState):
        """
        This node check checks the Weather report for today. It return hourly Temperature(celcius) and Percipitation information

        """
        print(" \nMade it into method: DataCollector.weather_node\n")


                # Populating Docstring prompt
        weather_prompt_formatted = weather_prompt.format(timezone=self.config['location'],latitude=self.config['home_location'][0]['latitude'],longitude=self.config['home_location'][0]['longitude'])
        
                # formatted response model
        response_model = await self.setLLM(new_model=True,response_format=Weather)
        
                # Model call
        agent_response = await response_model.ainvoke({"messages": [HumanMessage(content=weather_prompt_formatted)]},config=self.llmConfig)
        
                # Config assignment
        self.config["weather"] = agent_response["structured_response"].hourly_weather

        return state
    

    def saveConf(self,state: DayAgentState):
        """
        Saves config to work on MD maker.
        
        """
        print(" \nMade it into method: DataCollector.saveConf\n")

        dirname = os.path.dirname(__file__)
        
        if "/app" in dirname:
            dirname = dirname.replace("/app","")

        config_serializable = {
            "name": self.config["name"],
            "location": self.config["location"],
            "work_location": self.config["work_location"],
            "home_location": self.config["home_location"],
            "dentist_location": self.config["dentist_location"],
            "calendar_events": [event.model_dump() for event in self.config["calendar_events"]],
            "transportation_list": [t.model_dump() for t in self.config["transportation_list"]],
            "new_email": [mail.model_dump() for mail in self.config["new_email"].mails],
            "weather": [w.model_dump() for w in self.config["weather"]]
        }

        savePath =os.path.join(dirname,"result","results.json") 
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






async def run(obj: DayAgent):
    print(" \nMade it into method: Run\n")

    conf = {"configurable": {"thread_id": "1"}}
    inputs = {"messages": [HumanMessage(content="")]}
    await obj.graph.ainvoke(inputs,conf)



    
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
