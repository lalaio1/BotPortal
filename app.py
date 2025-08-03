import os
import discord
from discord.ext import commands
from flask import Flask, render_template, request, session, redirect, url_for, flash
import asyncio
import threading
import time
from queue import Queue
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./logs/bot_operations.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['TEMPLATES_AUTO_RELOAD'] = True

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

active_bots = {}
bot_queues = {}
bot_stats = {}
stop_flags = {}

class BotRunner(threading.Thread):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.bot = commands.Bot(
            command_prefix='!', 
            intents=intents,
            help_command=None
        )
        self.ready = False
        self.guilds = []
        self.queue = Queue()
        self.lock = threading.Lock()
        
        @self.bot.event
        async def on_ready():
            logging.info(f'Bot {self.bot.user} conectado!')
            self.ready = True
            self.guilds = list(self.bot.guilds)
            
            with self.lock:
                for guild in self.guilds:
                    bot_stats.setdefault(self.token, {})[guild.id] = {
                        'total': 0,
                        'success': 0,
                        'fails': 0,
                        'start_time': None,
                        'end_time': None
                    }
                    stop_flags.setdefault(self.token, {})[guild.id] = False

    def run(self):
        try:
            self.bot.run(self.token)
        except Exception as e:
            logging.error(f"Erro no bot {self.token[:15]}...: {str(e)}")

# ================== ROTAS FLASK ==================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('token', None)
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    token = request.form['token'].strip()
    if not token:
        flash('Token inválido!', 'danger')
        return redirect('/')
    
    session['token'] = token
    
    if token in active_bots:
        return redirect(url_for('list_servers'))
    
    bot_runner = BotRunner(token)
    active_bots[token] = bot_runner
    bot_runner.start()
    
    for _ in range(20):
        if bot_runner.ready:
            return redirect(url_for('list_servers'))
        time.sleep(1)
    
    flash('Falha na conexão. Verifique o token!', 'danger')
    return redirect('/')

@app.route('/servers')
def list_servers():
    token = session.get('token')
    if not token:
        return redirect('/')
    
    bot_runner = active_bots.get(token)
    if not bot_runner or not bot_runner.ready:
        return redirect('/')
    
    guilds_info = []
    for guild in bot_runner.guilds:
        members = guild.members
        online = sum(1 for m in members if not m.bot and m.status != discord.Status.offline)
        offline = sum(1 for m in members if not m.bot and m.status == discord.Status.offline)
        bots = sum(1 for m in members if m.bot)
        roles = len(guild.roles)
        channels = len(guild.channels)
        emojis = len(guild.emojis)
        created_at = guild.created_at.strftime('%d/%m/%Y')
        
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        
        stats = bot_stats.get(token, {}).get(guild.id, {})
        
        guilds_info.append({
            'id': guild.id,
            'name': guild.name,
            'icon': guild.icon.url if guild.icon else None,
            'owner': guild.owner.name if guild.owner else 'Desconhecido',
            'members': guild.member_count,
            'online': online,
            'offline': offline,
            'bots': bots,
            'roles': roles,
            'channels': channels,
            'emojis': emojis,
            'created_at': created_at,
            'boost_level': boost_level,
            'boost_count': boost_count,
            'stats': stats
        })
    
    return render_template('servers.html', guilds=guilds_info)

@app.route('/send/<int:guild_id>', methods=['POST'])
def send_messages(guild_id):
    token = session.get('token')
    if not token:
        return redirect('/')
    
    bot_runner = active_bots.get(token)
    if not bot_runner or not bot_runner.ready:
        return "Bot não disponível"
    
    message = request.form['message']
    delay = float(request.form.get('delay', 0.5))
    include_bots = 'include_bots' in request.form
    roles_filter = request.form.getlist('roles')
    
    stop_flags[token][guild_id] = False
    
    bot_stats[token][guild_id].update({
        'start_time': datetime.now().strftime('%H:%M:%S'),
        'total': 0,
        'success': 0,
        'fails': 0
    })
    
    bot_runner.queue.put((guild_id, message, delay, include_bots, roles_filter))
    
    flash('Envio iniciado! Verifique o console para detalhes.', 'success')
    return redirect(url_for('list_servers'))

@app.route('/stop/<int:guild_id>')
def stop_sending(guild_id):
    token = session.get('token')
    if token and token in stop_flags and guild_id in stop_flags[token]:
        stop_flags[token][guild_id] = True
        flash('Solicitação de parada enviada!', 'info')
    return redirect(url_for('list_servers'))

# ================== FUNÇÕES DE PROCESSAMENTO ==================
def process_queues():
    while True:
        for token, runner in list(active_bots.items()):
            try:
                while not runner.queue.empty():
                    task = runner.queue.get_nowait()
                    asyncio.run_coroutine_threadsafe(
                        send_dm_to_guild(runner.bot, token, *task), 
                        runner.bot.loop
                    )
            except Exception as e:
                logging.error(f"Erro no processamento: {str(e)}")
        time.sleep(0.5)

async def send_dm_to_guild(bot, token, guild_id, message, delay, include_bots, roles_filter):
    try:
        guild = discord.utils.get(bot.guilds, id=guild_id)
        if not guild:
            logging.error(f"Servidor {guild_id} não encontrado")
            return

        logging.info(f"Iniciando envio para: {guild.name}")
        stats = bot_stats.get(token, {}).get(guild_id, {})
        stats['total'] = 0
        stats['success'] = 0
        stats['fails'] = 0
        
        members = []
        for member in guild.members:
            if member.bot and not include_bots:
                continue
                
            if roles_filter:
                member_roles = [str(r.id) for r in member.roles]
                if not any(role in member_roles for role in roles_filter):
                    continue
                    
            members.append(member)
        
        stats['total'] = len(members)
        stop_flag = stop_flags.get(token, {}).get(guild_id, False)
        
        for index, member in enumerate(members):
            if stop_flag:
                logging.warning(f"Envio interrompido para {guild.name}")
                break
                
            try:
                personalized = message.replace("{user}", member.display_name)
                personalized = personalized.replace("{server}", guild.name)
                
                await member.send(personalized)
                stats['success'] += 1
                logging.info(f"+ [{index+1}/{len(members)}] {member}")
            except (discord.Forbidden, discord.HTTPException) as e:
                stats['fails'] += 1
                logging.warning(f"- [{index+1}/{len(members)}] {member} - {str(e)}")
            
            await asyncio.sleep(delay)
        
        stats['end_time'] = datetime.now().strftime('%H:%M:%S')
        logging.info(f"Concluído! Sucessos: {stats['success']}, Falhas: {stats['fails']}")
        
    except Exception as e:
        logging.critical(f"ERRO CRÍTICO: {str(e)}")
    finally:
        if token in stop_flags and guild_id in stop_flags[token]:
            stop_flags[token][guild_id] = False

# ================== INICIALIZAÇÃO ==================
if __name__ == '__main__':
    queue_thread = threading.Thread(target=process_queues, daemon=True)
    queue_thread.start()
    
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True,
        use_reloader=False,
        threaded=True
    )