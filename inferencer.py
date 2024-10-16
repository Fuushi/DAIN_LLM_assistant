from tools import Tools as TL
import copy
from classes import Logger as LG
class inference_wrapper:
    def __init__(self) -> None:
        #config
        pass

    def chat_generation(self, ctx) -> dict:

        r = inferencers.cloud.run_inference_with_tools(ctx)
        LG.log("LM End")

        return r
    

class inferencers:
    class cloud:
        def run_inference(ctx) -> dict:
            import openai
            import Keys
            keys=Keys.Keys()
            
            from openai import OpenAI
            client = OpenAI()
            client.api_key=keys.openai
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=ctx
            ).choices[0].message.content

            return {"role" : "assistant", "content" : r}
        
        def run_inference_with_tools(ctx, tools=None, verbose=True) -> dict:
            if verbose: LG.log("LM start")

            #define tools
            tools = TL.get_tools()

            #import dependancies
            import openai
            import Keys
            from openai import OpenAI

            #initialize objects
            keys=Keys.Keys()
            client = OpenAI()
            client.api_key=keys.openai

            #make tools inference (crop incoming ctx)
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=ctx,
                temperature=1,
                max_tokens=512,
                tools=tools
            )

            if r.choices[0].message.tool_calls:
                #if tools, pack results
                call_tools = r.choices[0].message.tool_calls[0].function.name
                args = r.choices[0].message.tool_calls[0].function.arguments
                if verbose: LG.log(call_tools, args)
            else:
                #else, return message 
                if verbose: LG.log(r.choices[0].message.content)
                return {"role" : "assistant", "content" : r.choices[0].message.content}

            #pack tools
            
            #run tools
            tool_results = TL.run_tools(call_tools, args)

            #if calls, insert tool response into new inference context
            if tools: ctx.append({"role" : "user", "content" : f"*result from function: {tool_results}*"})

            #run new inference with added info
            r2 = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=ctx,
                temperature=1,
                max_tokens=2048,
            )
            
            #pack new result
            message = {"role" : "assistant", "content" : r2.choices[0].message.content}
            
            #return
            if verbose: LG.log(message)
            return message



    class phi:
        def run_inference(ctx) -> None:
            #model is hotloaded, inferenced, then discarded

            #imports
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            import gc

            #initialize thread
            print("::DEBUG:: Starting inference")

            #load the model from huggingface
            model = AutoModelForCausalLM.from_pretrained(
                "microsoft/Phi-3-mini-4k-instruct", 
                device_map="cuda", 
                torch_dtype="auto", 
                trust_remote_code=True, 
            )
            tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")

            #create message context
            messages=ctx

            #create pipeline
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
            )

            #create configurator
            generation_args = {
                "max_new_tokens": 500,
                "return_full_text": False,
                "temperature": 0.0,
                "do_sample": False,
            }

            #inference model
            output = pipe(messages, **generation_args)

            #unload model from memory
            model.to('meta')

            #clean up function before returning
            torch.cuda.empty_cache()
            del model
            gc.collect()

            #return
            print("::DEBUG:: Completed inference")
            return {"role" : "assistant", "content" : output[0]['generated_text']}
        

class Contextualizer:
    #crops ctx to message or token limit, whichever comes first
    #(first message is guarenteed)
    def crop_ctx(ctx, messages=100, tokens=1024*8, chars=1024*16):

        #deep copy ctx
        c = copy.deepcopy(ctx)

        #create empty return array
        arr=[]

        #reverse array
        c = c[::-1]

        #append first message (first message is guarenteed)
        arr.append(c[0]); c.remove(c[0])

        #iterate
        for m in c:
            sample = arr+[m]

            #test sample
            
            #arr length
            if len(sample) >= messages: 
                break
            #char length
            foo=0
            for M in sample: foo+=len(M['content'])
            if foo >= chars: 
                break
            #token length
            pass

            #append
            arr.append(m)

        #arr is reversed, reverse again to fix order
        arr=arr[::-1]

        #debug, print details
        print(f"Message cropped to {len(arr)} messages")

        #return new array
        return arr





