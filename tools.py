import requests, json
from classes import Logger as LG
from Keys import Keys
keys=Keys()

class Tools:
    #def get_current_weather(location):
    #    location = "The weather is 28*C and sunny."
    #    return location
    

    def get_current_weather(location):
        LG.log("Getting weather")
        api_key = keys.weather  # Replace with your actual API key

        #parse location
        location = json.loads(location)['location'].replace(" ", "").split(",")[0]



        #geocode
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&appid={api_key}"

        response = requests.get(geocode_url)

        data = response.json()

        if (not response.ok) or (not data):
            r="City not found or weather data unavailable."
            LG.log(r)
            return r


        ##unpack geocoding data
        lat=data[0]['lat']
        lon=data[0]['lon']
        

        #weather call
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"

        response = requests.get(weather_url)

        data = response.json()

        if (not response.ok) or (not data):
            r="City not found or weather data unavailable."
            LG.log(r)
            return r

        #unpack weather response
        location=location
        temperature=data['main']['temp']-272.15
        weather_desc=data['weather'][0]['description']

        r=f"The weather in {location} is {temperature}°C with {weather_desc}."
        LG.log(r)
        return r
    

    #
    def dispatch_agent(task, details=None):
        LG.log(f"Dispatching agent to: {task}")

        #parse request
        task = json.loads(task)['task'] + ", Ask for no further assistance unless mission critical"

        #
        from interpreter import interpreter
        interpreter.llm.api_key=keys.openai
        interpreter.llm.model="gpt-4o-mini"

        interpreter.auto_run=True
        
        r = interpreter.chat(task)

        return f"function call results: {r}"
    

    #
    def media_controls(action, details=None):
        LG.log(f"LLM attempted media controls")
        import ctypes
        import time

        #parse request
        action = json.loads(action)["task"]

        # Constants for media keys (using Windows VK codes)
        VK_MEDIA_PLAY_PAUSE = 0xB3
        VK_MEDIA_NEXT_TRACK = 0xB0
        VK_MEDIA_PREV_TRACK = 0xB1

        # Press a media key
        def press_media_key(vk_code):
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)  # Key down
            time.sleep(0.05)  # Small delay
            ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)  # Key up

        if action == "Play": press_media_key(VK_MEDIA_PLAY_PAUSE)

        elif action == "Pause": press_media_key(VK_MEDIA_PLAY_PAUSE)

        elif action == "Skip": press_media_key(VK_MEDIA_NEXT_TRACK)

        elif action == "Previous": press_media_key(VK_MEDIA_PREV_TRACK)

        else: return "Invalid Action, advice user."

        return "Function call completed Successfully, please advice the user"
    
    def web_search(query_string):
        LG.log(f"Web query for: {query_string}")
        from googleapiclient.discovery import build

        # Replace with your Google API Key and Custom Search Engine ID
        api_key = keys.google_search
        cse_id = keys.google_search_id

        def google_search(query : str, api_key, cse_id) -> dict:
            # Build the custom search service
            service = build("customsearch", "v1", developerKey=api_key)

            # Execute the search request
            response = service.cse().list(
                q=query,        # Search query
                cx=cse_id,      # Custom Search Engine ID
            ).execute()

            if response.get("items", False):
                return response['items']
            else:
                return []
        

        # Example search query
        results = google_search(query_string, api_key, cse_id)

        if not results:
            return "Function result: no search results found"

        # Parse the search results
        r=""
        for result in results:
            print(f"Title: {result['title']}")
            print(f"Link: {result['link']}")
            print(f"Snippet: {result['snippet']}")
            print()

            #naive string return, need to webscrape
            r += f"{result['title']} @ {result['link']}: {result['snippet']}"



        return "*results from websearch function: {r}*"
    
    def send_message(message):
        #DEPRECIATED
        print(f"Message from Assistant: {message}")
        return f"Message sent to user."



    
    def get_tools():
        with open("tools.json", 'r') as fp: return json.loads(fp.read())

    
    def run_tools(name, args):
        if name == "get_current_weather":
            return Tools.get_current_weather(args)
        
        elif name == "dispatch_agent":
            return Tools.dispatch_agent(args)
        
        elif name == "media_controls":
            return Tools.media_controls(args)
        
        elif name == "web_search":
            return Tools.web_search(args)
        
        elif name == "send_message":
            return Tools.send_message(args)
        
        else:
            print(f"WARNING: the agent has requested an invalid tool, {name}, {args}")
            return "no tool found, please ignore"