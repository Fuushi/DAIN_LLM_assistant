##

import os, sys, json, time
from threading import Thread
from inferencer import inference_wrapper

IW=inference_wrapper()

class Tasks:
    #tasks have scoped memory 
    class Dialogue:
        def __init__(self) -> None:
            self.type ="dialogue"
            self.completed=False
            self.timestamp=time.time()

        def run(self, state):
            #build context
            ctx = state.schema.buildctx()

            #inference
            resp = IW.chat_generation(ctx)

            #push response to io field
            state.io_to_terminal.append(resp)

            #add to mem
            state.schema.shortTermMemory.append(resp)

    class UpdateUserData:
        def __init__(self) -> None:
            self.type="update"
            self.completed=False
            self.timestamp=time.time()

        def run(self, state):
            #print("Updating internal registry")
            #updates internal registry
            #-> user location
            #-> user network status
            #-> time
            state.schema.facts['epoch']=time.time()
            return


            

class Schema:
    def __init__(self) -> None:
        self.taskList=[]
        self.shortTermMemory=[] #contains misc info, not just dialogue
        self.longTermInMemory=[] #long term memory loaded, updates occasionally
        self.facts={}
        pass

    def dialogue(self, message : dict) -> dict:
        #inferences dialogue based on current memory.
        self.taskList.append(Tasks.Dialogue())
        self.shortTermMemory.append(message)

        return
    
    def buildctx(self) -> list:
        #naive approach (essentially just a deep copy of short term)
        ctx=[{"role" : "system", "content" : "You are an Autonymous agent and are running in loop, your personality is akin to Jarvis, or the computer from Hitchhikers guide to the galaxy. Use Function calls when helpfull."}]
        ctx=[]
        for mem in self.shortTermMemory:
            ctx.append(mem)

        return ctx
    



class State:
    def __init__(self) -> None:
        self.schema=Schema()
        self.io_to_terminal=[]
        return
    
state=State()




class threads:
    def IOthread(state):

        while True:
            #print("IO-tick")
            #poll user input
            foo = input("\nUser: ")

            #commit to model
            state.schema.dialogue({"role" : "user", "content" : foo})

            #wait for response
            while True:
                if state.io_to_terminal:
                    r=state.io_to_terminal[0]
                    break
                
                time.sleep(1)
            
            #print response
            print(f"Agent: {r['content']}")

            #clear io cache
            state.io_to_terminal.remove(r)

            #wait before next tick
            time.sleep(1)
            

    def backendthread(state):
        #this thread performs all processing and handles task loop

        while True: #task loop
            #print("BE-tick")

            #poll state for for tasks
            if state.schema.taskList: #if len > 1
                
                #get task
                localtask=state.schema.taskList[0]

                #remove from list
                state.schema.taskList.remove(localtask)
                
                #perform task
                localtask.run(state)

            #schedule tasks

            #schedule update if none scheduled
            updateScheduled=False
            for task in state.schema.taskList: 
                if task.type=="update":
                    updateScheduled=True

            if not updateScheduled: state.schema.taskList.append(Tasks.UpdateUserData())

            #diag
            #print(len(state.schema.taskList))


            #inference

            time.sleep(1)

def main():
    IO=Thread(target=threads.IOthread, args=(state,))
    IO.daemon=True
    IO.start()

    BE=Thread(target=threads.backendthread, args=(state,))
    BE.daemon=True
    BE.start()

    while True:
        #print("MN-tick")
        if (not IO.is_alive()) or (not BE.is_alive()):
            print("A thread has exited, returning")
            break

        time.sleep(1)

    return

if __name__ == "__main__":
    main()