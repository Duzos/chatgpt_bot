import discord
import openai
import json
from discord.ext import commands

# Get information from config
with open('config.json','r') as f:
    config = json.load(f)

TOKEN = config["token"]
OPENAI_KEY = config["openai_key"]

# Setup OpenAI
openai.api_key = OPENAI_KEY
openai_engine = "text-davinci-003"

# Setup discord client
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!',intents=intents)

# Define a function that generates a response from the OpenAI API
async def generate_response(message, prompt: str = None):
    if prompt == None:
        prompt = f"{message.content}\nAI:"
    response = openai.Completion.create(
        engine=openai_engine,
        prompt=prompt,
        max_tokens=256,
        n=1,
        stop=None,
        temperature=1,
    )
    return response.choices[0].text.strip()

async def generate_response_with_history(message: discord.Message,thread: discord.Thread):
    messages = [message async for message in thread.history()]
    messages.pop(0)
    messages.reverse()
    messages_string = "CHAT HISTORY:"

    for msg in messages:
        messages_string += f'\n{msg.content}'
    
    query = messages_string + "\nQuery: " + message.content + "\nAI: "

    response = await generate_response(message, query)
    return response

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Check to see if we are processing OpenAI on this message
    if type(message.channel) == discord.Thread: 
        # Check if it was made by dubot
        thread = message.channel
        
        if thread.owner_id == bot.user.id:
            # Check to see if it begins with "AI"
            if thread.name[:2] == "AI":
                async with thread.typing():
                    response = await generate_response_with_history(message, thread)
                await message.reply(response)

    await bot.process_commands(message)

@bot.command()
async def ask(ctx, *, prompt):
    async with ctx.channel.typing():
        response = await generate_response(ctx, prompt)
    
    NAME_LIMIT = 100
    name = f"AI: {ctx.message.content}"
    if len(name) > NAME_LIMIT:
        name = name[0:NAME_LIMIT]
    thread = await ctx.message.create_thread(name=name,auto_archive_duration = 60)

    await thread.send(content=response)

bot.run(TOKEN)