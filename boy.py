from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_button, create_actionrow, create_select, create_select_option
import sqlite3
import datetime
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix="!")
slash = SlashCommand(bot, sync_commands=True)

# Configuração do banco de dados SQLite
conn = sqlite3.connect('tickets.db')
c = conn.cursor()

# Criação da tabela de tickets (caso não exista)
c.execute('''CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticket_channel_id INTEGER,
                status TEXT,
                category TEXT,
                description TEXT,
                timestamp TEXT
             )''')

# Criação da tabela de histórico de tickets (caso não exista)
c.execute('''CREATE TABLE IF NOT EXISTS ticket_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticket_channel_id INTEGER,
                status TEXT,
                category TEXT,
                description TEXT,
                timestamp TEXT
             )''')

# Função para inserir um novo ticket no banco de dados
def insert_ticket(user_id, ticket_channel_id, status, category, description):
    timestamp = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO tickets (user_id, ticket_channel_id, status, category, description, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, ticket_channel_id, status, category, description, timestamp))
    conn.commit()

# Função para atualizar o status de um ticket no banco de dados
def update_ticket_status(ticket_channel_id, status):
    timestamp = datetime.datetime.now().isoformat()
    c.execute("UPDATE tickets SET status = ?, timestamp = ? WHERE ticket_channel_id = ?", (status, timestamp, ticket_channel_id))
    conn.commit()

# Função para mover um ticket para o histórico
def move_ticket_to_history(ticket_channel_id):
    c.execute("INSERT INTO ticket_history SELECT * FROM tickets WHERE ticket_channel_id = ?", (ticket_channel_id,))
    c.execute("DELETE FROM tickets WHERE ticket_channel_id = ?", (ticket_channel_id,))
    conn.commit()

# Função para obter informações de um ticket pelo ID do canal
def get_ticket_by_channel_id(ticket_channel_id):
    c.execute("SELECT * FROM tickets WHERE ticket_channel_id = ?", (ticket_channel_id,))
    return c.fetchone()

# Função para obter informações de todos os tickets de um usuário
def get_tickets_by_user(user_id):
    c.execute("SELECT * FROM tickets WHERE user_id = ? AND status = 'Aberto'", (user_id,))
    return c.fetchall()

# Função para obter o histórico de tickets de um usuário
def get_ticket_history_by_user(user_id):
    c.execute("SELECT * FROM ticket_history WHERE user_id = ?", (user_id,))
    return c.fetchall()

# Função para enviar uma mensagem de log
async def send_log_message(content):
    log_channel = discord.utils.get(bot.get_all_channels(), name="ticket-logs")
    if not log_channel:
        for guild in bot.guilds:
            log_channel = await guild.create_text_channel('ticket-logs')
            break
    await log_channel.send(content)

# Função para resposta automática
def auto_reply(category, description):
    if category == "Pergunta":
        return "Aqui está a resposta para sua pergunta..."
    elif "palavra-chave" in description:
        return "Parece que você está tendo problemas com a palavra-chave..."
    else:
        return None

# Função para criar um menu suspenso com categorias
def create_category_select():
    options = [
        create_select_option("Pergunta", value="Pergunta"),
        create_select_option("Relatório de bug", value="Relatório de bug"),
        create_select_option("Solicitação de recurso", value="Solicitação de recurso")
    ]
    select = create_select(options=options, placeholder="Escolha uma categoria", min_values=1, max_values=1)
    return create_actionrow(select)

@bot.command(name='createticketmessage')
async def create_ticket_message(ctx):
    channel = bot.get_channel(id_do_canal)  # Substitua id_do_canal pelo ID do canal onde você quer enviar a mensagem
    buttons = [
        create_button(
            style=ButtonStyle.green,
            label="Criar Ticket",
            custom_id="create_ticket"
        )
    ]
    action_row = create_actionrow(*buttons)
    await channel.send(content="Clique no botão abaixo para criar um ticket:", components=[action_row])

@slash.component()
async def create_ticket(ctx: SlashContext):
    category_select = create_category_select()
    await ctx.send(content="Escolha uma categoria para o seu ticket:", components=[category_select])

@slash.component()
async def on_select(ctx: SlashContext):
    category = ctx.selected_options[0]
    description = "Descrição do ticket"  # Você pode substituir isso por uma descrição
