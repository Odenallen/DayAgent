

# TODO
## MCP
- MCP Google Calendar Server (Done)
- Gmail MCP server up and running(Done)
    - Read emails from the correct day(Not working)
    - Come up with way to get LLM to summerize email from correct day.
    - Get working MCP server. (Done)

- Weather MCP server Running (Done)
    - Get weather for specific location today.(Done)
    - Get weather for specific location at specific date.(Done)
    - Get Precipitation Rate (Done)

- MarkDown to PDF MCP server.(Done)
    - Working with readme file(Done)

- Google Tasks?
    - For reminder

## Alpha

### Testing
- [x] Jinja2 Template
  - [x] No class
  - [x] Simple class
  - [x] Nested classed 
- [ ] Memory


### bot.py
- [x] Config loading
- [x] conf -> Class
- [x] Memory

### ClassStructs
- [x] Mail Class implemented
- [x] Mail Class tested
- [x] MDdata Complete

### General
- [ ] Decide if we want pdf generation or stick with MD
- [ ] Token refresh for each tool!

### State of affair

  - [x] Make structured_response part of data.
  - [x] How should I handle the class of the calendar events? (Maybe fixed)
  - [x] Generate prompt for transportation node.
  - [ ]  
  - [ ] Understand why LLM call sending warnings

## Beta
### Beta implementations
 - [ ] Use SL API Instead of Google Maps for transportation?
 - [ ] Use MCP tool to use webb to find lat and long if the weather tool does not provide one.



# GitHub länkar
- https://github.com/GongRzhe/Gmail-MCP-Server?tab=readme-ov-file
- https://github.com/WeatherXM/weatherxm-pro-mcp
- https://github.com/seanivore/Convert-Markdown-PDF-MCP
- https://github.com/nspady/google-calendar-mcp
- https://github.com/modelcontextprotocol/servers-archived/tree/main/src/google-maps

# Websidor
- https://pro.weatherxm.com/?station=scruffy-maize-cirrostratus
- https://www.trafiklab.se/sv/api/our-apis/sl/transport/



# Later
- Script hiding all API keys and json files with keys
- Understand why its printing things like:
    "Key '$schema' is not supported in schema, ignoring
    Key 'additionalProperties' is not supported in schema, ignoring
    Key '$schema' is not supported in schema, ignoring"


# Prompts


## weatherxm-pro-mcp

what is the weather forcast for the station with station id: 85a88940-4df3-11ed-960b-b351f0b0cc44, check precipitation , starting on the 17th of september 2025 and ends with the 18th of september 2025, I would like the forecast to be hourly. Be careful with the parameters, make sure they are correctly named, example:
{'forecast_to': '2025-09-18', 'forecast_from': '2025-09-17', 'forecast_cell_index': '85a88940-4df3-11ed-960b-b351f0b0cc44', 'forecast_include': 'hourly'}

what is the weather forcast for the station with station id: 85a88940-4df3-11ed-960b-b351f0b0cc44, check temperature, precipitation and windSpeed, starting on the 17th of september 2025 and ends with the 18th of september 2025, I would like the forecast to be hourly. Be careful with the parameters, make sure they are correctly named, example:
{'forecast_to': '2025-09-18', 'forecast_from': '2025-09-17', 'forecast_cell_index': '85a88940-4df3-11ed-960b-b351f0b0cc44', 'forecast_include': 'hourly'}. Make seperate calls for each variable with the given information if it is needed. Also present the information formatted for each day.



## markdown2pdf

Can you make a pdf from the markdown:  " # TEST MARKDOWN2PDF \\n ##Working?". Call it "markdown2pdf-test", no date needed. Store this in the '/home/oden/Documents/Code/AI_Agents/DayAgent/pdfs' folder'

## Gmail


show me the raw output you get when you query about the email with message id: 1995d921db9f08b9'. Give it to me in the exakt form the MCP tool gives you

## Google Maps

