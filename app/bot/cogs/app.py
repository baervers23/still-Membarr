from pickle import FALSE
import app.bot.helper.jellyfinhelper as jelly
from app.bot.helper.textformat import bcolors
import discord
from discord.ext import commands
from discord.ui import View, button, Button
from discord import app_commands, Interaction, ButtonStyle, Intents
import asyncio
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
import app.bot.helper.db as db
import app.bot.helper.plexhelper as plexhelper
import app.bot.helper.jellyfinhelper as jelly
import texttable
from app.bot.helper.message import *
from app.bot.helper.confighelper import *

CONFIG_PATH = 'app/config/config.ini'
BOT_SECTION = 'bot_envs'

plex_configured = True
jellyfin_configured = True

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

plex_token_configured = True
try:
    PLEX_TOKEN = config.get(BOT_SECTION, 'plex_token')
    PLEX_BASE_URL = config.get(BOT_SECTION, 'plex_base_url')
except:
    print("No Plex auth token details found")
    plex_token_configured = False

# Get Plex config
try:
    PLEXUSER = config.get(BOT_SECTION, 'plex_user')
    PLEXPASS = config.get(BOT_SECTION, 'plex_pass')
    PLEX_SERVER_NAME = config.get(BOT_SECTION, 'plex_server_name')
except:
    print("No Plex login info found")
    if not plex_token_configured:
        print("Could not load plex config")
        plex_configured = False

# Get Plex roles config
try:
    plex_roles = config.get(BOT_SECTION, 'plex_roles')
except:
    plex_roles = None
if plex_roles:
    plex_roles = list(plex_roles.split(','))
else:
    plex_roles = []

# Get Plex libs config
try:
    Plex_LIBS = config.get(BOT_SECTION, 'plex_libs')
except:
    Plex_LIBS = None
if Plex_LIBS is None:
    Plex_LIBS = ["all"]
else:
    Plex_LIBS = list(Plex_LIBS.split(','))
    
# Get Jellyfin config
try:
    JELLYFIN_SERVER_URL = config.get(BOT_SECTION, 'jellyfin_server_url')
    JELLYFIN_API_KEY = config.get(BOT_SECTION, "jellyfin_api_key")
except:
    jellyfin_configured = False

# Get Jellyfin roles config
try:
    jellyfin_roles = config.get(BOT_SECTION, 'jellyfin_roles')
except:
    jellyfin_roles = None
if jellyfin_roles:
    jellyfin_roles = list(jellyfin_roles.split(','))
else:
    jellyfin_roles = []

# Get Jellyfin libs config
try:
    jellyfin_libs = config.get(BOT_SECTION, 'jellyfin_libs')
except:
    jellyfin_libs = None
if jellyfin_libs is None:
    jellyfin_libs = ["all"]
else:
    jellyfin_libs = list(jellyfin_libs.split(','))

# Get Enable config
try:
    USE_JELLYFIN = config.get(BOT_SECTION, 'jellyfin_enabled')
    USE_JELLYFIN = USE_JELLYFIN.lower() == "true"
except:
    USE_JELLYFIN = False

try:
    USE_PLEX = config.get(BOT_SECTION, "plex_enabled")
    USE_PLEX = USE_PLEX.lower() == "true"
except:
    USE_PLEX = False

try:
    JELLYFIN_EXTERNAL_URL = config.get(BOT_SECTION, "jellyfin_external_url")
    if not JELLYFIN_EXTERNAL_URL:
        JELLYFIN_EXTERNAL_URL = JELLYFIN_SERVER_URL
except:
    JELLYFIN_EXTERNAL_URL = JELLYFIN_SERVER_URL
    print("Could not get Jellyfin external url. Defaulting to server url.")

if USE_PLEX and plex_configured:
    try:
        print("Connecting to Plex......")
        if plex_token_configured and PLEX_TOKEN and PLEX_BASE_URL:
            print("Using Plex auth token")
            plex = PlexServer(PLEX_BASE_URL, PLEX_TOKEN)
        else:
            print("Using Plex login info")
            account = MyPlexAccount(PLEXUSER, PLEXPASS)
            plex = account.resource(PLEX_SERVER_NAME).connect()  # returns a PlexServer instance
        print('Logged into plex!')
    except Exception as e:
        # probably rate limited.
        print('Error with plex login. Please check Plex authentication details. If you have restarted the bot multiple times recently, this is most likely due to being ratelimited on the Plex API. Try again in 10 minutes.')
        print(f'Error: {e}')
else:
    print(f"Plex {'disabled' if not USE_PLEX else 'not configured'}. Skipping Plex login.")

class app(commands.Cog):
    # App command groups
    plex_commands = app_commands.Group(name="plex", description="Membarr Plex commands")
    jellyfin_commands = app_commands.Group(name="jellyfin", description="Membarr Jellyfin commands")
    membarr_commands = app_commands.Group(name="membarr", description="Membarr general commands")

    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print('------')
        print("{:^41}".format(f"MEMBARR V {MEMBARR_VERSION}"))
        print(f'Modified by Baervers23 https://github.com/baervers23/')
        print(f'Forked from & Original by Yoruio https://github.com/Yoruio/\n')
        print(f'Forked from Invitarr https://github.com/Sleepingpirates/Invitarr')
        print(f'Named by lordfransie')
        print(f'Logged in as {self.bot.user} (ID: {self.bot.user.id})')
        print('------')

        # TODO: Make these debug statements work. roles are currently empty arrays if no roles assigned.
        if plex_roles is None:
            print('Configure Plex roles to enable auto invite to Plex after a role is assigned.')
        if jellyfin_roles is None:
            print('Configure Jellyfin roles to enable auto invite to Jellyfin after a role is assigned.')
    
    async def getemail(self, after):
        email = None
        await embedinfo(after,'Welcome To '+ PLEX_SERVER_NAME +'. Please reply with your email to be added to the Plex server!')
        await embedinfo(after,'If you do not respond within 24 hours, the request will be cancelled, and the server admin will need to add you manually.')
        while(email == None):
            def check(m):
                return m.author == after and not m.guild
            try:
                email = await self.bot.wait_for('message', timeout=86400, check=check)
                if(plexhelper.verifyemail(str(email.content))):
                    return str(email.content)
                else:
                    email = None
                    message = "The email you provided is invalid, please respond only with the email you used to sign up for Plex."
                    await embederror(after, message)
                    continue
            except asyncio.TimeoutError:
                message = "Timed out. Please contact the server admin directly."
                await embederror(after, message)
                return None
    
    async def getusername(self, after):
        username = None
        await embedinfo(after, f"Willkommen auf meinem Jellyfin-Server! Gerne helfe ich dir, deinen Account zu erstellen.")
        await embedinfo(after, f"Wie soll dein Benutzername lauten?")
        await embedinfo(after, f"Info: Wenn du nicht innerhalb von 24 Stunden antwortest, wird der Vorgang abgebrochen und du musst den Admin bitten, dir manuell einen Account zu erstellen.")
        while (username is None):
            def check(m):
                return m.author == after and not m.guild
            try:
                username = await self.bot.wait_for('message', timeout=86400, check=check)
                if(jelly.verify_username(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, str(username.content))):
                    return str(username.content)
                else:
                    username = None
                    message = "⚠️  Der Benutzername ist bereits vergeben!"
                    await embederror(after, message)
                    continue
            except asyncio.TimeoutError:
                message = "❌  Zeit abgelaufen, bitte kontaktiere den Admin"
                print("Jellyfin Benutzernamen Eingabe abgelaufen")
                await embederror(after, message)
                return None
            except Exception as e:
                await embederror(after, "❌  Leider ist etwas schief gelaufen, probiere bitte einen anderen Benutzernamen!")
                print (e)
                username = None


    async def addtoplex(self, email, response):
        if(plexhelper.verifyemail(email)):
            if plexhelper.plexadd(plex,email,Plex_LIBS):
                await embedinfo(response, 'This email address has been added to plex')
                return True
            else:
                await embederror(response, 'There was an error adding this email address. Check logs.')
                return False
        else:
            await embederror(response, 'Invalid email.')
            return False

    async def removefromplex(self, email, response):
        if(plexhelper.verifyemail(email)):
            if plexhelper.plexremove(plex,email):
                await embedinfo(response, 'This email address has been removed from plex.')
                return True
            else:
                await embederror(response, 'There was an error removing this email address. Check logs.')
                return False
        else:
            await embederror(response, 'Invalid email.')
            return False
    
    async def addtojellyfin(self, username, password, response):
        if not jelly.verify_username(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username):
            await embederror(response, f'⚠️  Es existier bereits ein Account mit dem Benutzernamen: {username}.')
            return False

        if jelly.add_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username, password, jellyfin_libs):
            return True
        else:
            await embederror(response, '❌  Fehler beim hinzufügen des Benutzers. Check logs for more info.')
            return False

    async def resetpwjellyfin(self, username, password):
        return jelly.reset_pw(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username, password)

    async def removefromjellyfin(self, username, response):
        if jelly.verify_username(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username):
            await embederror(response, f'❌  Mir ist kein Account mit dem Benutzernamen: {username} bekannt.')
            return
        
        if jelly.remove_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username):
            await embedinfo(response, f'✅  Der Benutzer {username} wurde von Jellifin entfernt.')
            return True
        else:
            await embederror(response, f'❌  Leider ist beim entfernen des Benutzers ein Fehler unterlaufen. Infos siehe logs.')
            return False

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if plex_roles is None and jellyfin_roles is None:
            return
        roles_in_guild = after.guild.roles
        role = None
        #tmp = None

        plex_processed = False
        jellyfin_processed = False

        # Check Plex roles
        if plex_configured and USE_PLEX:
            for role_for_app in plex_roles:
                for role_in_guild in roles_in_guild:
                    if role_in_guild.name == role_for_app:
                        role = role_in_guild

                    # Plex role was added
                    if role is not None and (role in after.roles and role not in before.roles):
                        email = await self.getemail(after)
                        if email is not None:
                            await embedinfo(after, "Got it we will be adding your email to plex shortly!")
                            if plexhelper.plexadd(plex,email,Plex_LIBS):
                                db.save_user_email(str(after.id), email)
                                await asyncio.sleep(5)
                                await embedinfo(after, 'You have Been Added To Plex! Login to plex and accept the invite!')
                            else:
                                await embedinfo(after, 'There was an error adding this email address. Message Server Admin.')
                        plex_processed = True
                        break

                    # Plex role was removed
                    elif role is not None and (role not in after.roles and role in before.roles):
                        try:
                            user_id = after.id
                            email = db.get_useremail(user_id)
                            plexhelper.plexremove(plex,email)
                            deleted = db.remove_email(user_id)
                            if deleted:
                                print("Removed Plex email {} from db".format(after.name))
                                #await secure.send(plexname + ' ' + after.mention + ' was removed from plex')
                            else:
                                print("Cannot remove Plex from this user.")
                            await embedinfo(after, "You have been removed from Plex")
                        except Exception as e:
                            print(e)
                            print("{} Cannot remove this user from plex.".format(email))
                        plex_processed = True
                        break
                if plex_processed:
                    break

        role = None
        # Check Jellyfin roles
        if jellyfin_configured and USE_JELLYFIN:
            for role_for_app in jellyfin_roles:
                for role_in_guild in roles_in_guild:
                    if role_in_guild.name == role_for_app:
                        role = role_in_guild

                    # Role was added check first time or reactivation
                    if role is not None and (role in after.roles and role not in before.roles):
                        print("Jellyfin Role hinzugefügt")
                        try:
                            user_id = after.id
                            username = db.get_jellyfin_username(user_id)
                            if jelly.enable_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username):
                                await embedinfo(after, "✅Jellyfin wurde wieder aktiviert.")
                                await embedinfo(after, f"Du kannst dich wieder bei {JELLYFIN_EXTERNAL_URL} einloggen!")
                            elif jelly.enable_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username) is False:
                                await embedcustom(after, "❌  KILL TASK")
                        except Exception as e:                                
                            print("Erstanmeldung")
                            username = await self.getusername(after)
                            if username is not None:
                                #await embedinfo(after, f"Alles klar, Benutzernamen: {username}, Passwort wird generiert.")
                                password = jelly.generate_password(16)
                                if jelly.add_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username, password, jellyfin_libs):
                                    db.save_user_jellyfin(str(after.id), username)
                                    await asyncio.sleep(5)
                                    await embedcustom(after, "✅  Benutzer wurde erfolgreich erstellt.", {'Username': username, 'Passwort': f"||{password}||"})
                                    await embedinfo(after, f"Du kannst dich unter {JELLYFIN_EXTERNAL_URL} einloggen!")
                                else:
                                    await embedinfo(after, "❌  Error: Account konnte nicht erstellt werden. Server URL muss mit 'https://' angegeben werden.")
                            jellyfin_processed = True
                            break  
                        jellyfin_processed = True
                        break
                        
                    elif role is not None and (role not in after.roles and role in before.roles):
                        print("Jellyfin Role entfernt.")
                        try:
                            user_id = after.id
                            username = db.get_jellyfin_username(user_id)
                            jelly.disable_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username)
                            await embedinfo(after, "❌  Dein Jellyfin Benutzer wurde deaktiviert")
                        except Exception as e:
                            print(e)
                            print("❌  Fehler beim deaktivieren von Jellyfin: '{}'".format(username))
                        jellyfin_processed = True
                        break
                    
                if jellyfin_processed:
                    break


    @jellyfin_commands.command(name="resetpassword", description="Wenn du dein Passwort vergessen hast kannst du es hier resetten.")
    async def resetpw(self, interaction: discord.Interaction): 
        await interaction.response.defer(ephemeral=True)

        password = jelly.generate_password(16)
        username = db.get_jellyfin_username(interaction.user.id)
    
        if not username:
            await embederror(interaction, "❌  Kein verknüpfter Jellyfin-Account gefunden.")
            return

        try:
            success = await self.resetpwjellyfin(username, password)
            if success:
                try:
                    message = (
                        f"**Neues Passwort:** ||{password}||"
                    )
                    await interaction.user.send(message)
                    await interaction.followup.send("✅   Dein neues Passwort wurde dir per DM geschickt.")
                except discord.Forbidden:
                    await interaction.followup.send("⚠️   Konnte dir keine DM senden. Aktiviere bitte private Nachrichten von Servermitgliedern.")
            else:
                await interaction.followup.send("❌   Passwort konnte nicht zurückgesetzt werden.")
        except Exception as e:
            print(e)
            await interaction.followup.send("❌   Beim Passwort zurücksetzen ist ein Fehler aufgetreten.")

    @app_commands.checks.has_permissions(administrator=True)
    @plex_commands.command(name="invite", description="Invite a user to Plex")
    async def plexinvite(self, interaction: discord.Interaction, email: str):
        await self.addtoplex(email, interaction.response)
    
    @app_commands.checks.has_permissions(administrator=True)
    @plex_commands.command(name="remove", description="Remove a user from Plex")
    async def plexremove(self, interaction: discord.Interaction, email: str):
        await self.removefromplex(email, interaction.response)
    
    @app_commands.checks.has_permissions(administrator=True)
    @jellyfin_commands.command(name="invite", description="Invite a user to Jellyfin")
    async def jellyfininvite(self, interaction: discord.Interaction, username: str):
        password = jelly.generate_password(16)
        if await self.addtojellyfin(username, password, interaction.response):
            await embedinfo(interaction.response, 'Jellyfin user created!', {'Username': username, 'Password': f'||{password}||'})

    @app_commands.checks.has_permissions(administrator=True)
    @jellyfin_commands.command(name="remove", description="Remove a user from Jellyfin")
    async def jellyfinremove(self, interaction: discord.Interaction, username: str):
        await self.removefromjellyfin(username, interaction.response)
    
    @app_commands.checks.has_permissions(administrator=True)
    @membarr_commands.command(name="dbadd", description="Add a user to the Membarr database")
    async def dbadd(self, interaction: discord.Interaction, member: discord.Member, email: str = "", jellyfin_username: str = ""):
        email = email.strip()
        jellyfin_username = jellyfin_username.strip()
        
        # Check email if provided
        if email and not plexhelper.verifyemail(email):
            await embederror(interaction.response, "Invalid email.")
            return

        try:
            db.save_user_all(str(member.id), email, jellyfin_username)
            await embedinfo(interaction.response,'User was added to the database.')
        except Exception as e:
            await embedinfo(interaction.response, 'There was an error adding this user to database. Check Membarr logs for more info')
            print(e)

    @app_commands.checks.has_permissions(administrator=True)
    @membarr_commands.command(name="dbls", description="View Membarr database")
    async def dbls(self, interaction: discord.Interaction):

        embed = discord.Embed(title='Membarr Database.')
        all = db.read_all()
        table = texttable.Texttable()
        table.set_cols_dtype(["t", "t", "t", "t"])
        table.set_cols_align(["c", "c", "c", "c"])
        header = ("#", "Name", "Email", "Jellyfin")
        table.add_row(header)
        for index, peoples in enumerate(all):
            index = index + 1
            id = int(peoples[1])
            dbuser = self.bot.get_user(id)
            dbemail = peoples[2] if peoples[2] else "No Plex"
            dbjellyfin = peoples[3] if peoples[3] else "No Jellyfin"
            try:
                username = dbuser.name
            except:
                username = "User Not Found."
            embed.add_field(name=f"**{index}. {username}**", value=dbemail+'\n'+dbjellyfin+'\n', inline=False)
            table.add_row((index, username, dbemail, dbjellyfin))
        
        total = str(len(all))
        if(len(all)>25):
            f = open("db.txt", "w")
            f.write(table.draw())
            f.close()
            await interaction.response.send_message("Database too large! Total: {total}".format(total = total),file=discord.File('db.txt'), ephemeral=True)
        else:
            await interaction.response.send_message(embed = embed, ephemeral=True)
        
            
    @app_commands.checks.has_permissions(administrator=True)
    @membarr_commands.command(name="dbrm", description="Remove user from Membarr database")
    async def dbrm(self, interaction: discord.Interaction, position: int):
        embed = discord.Embed(title='Membarr Database.')
        all = db.read_all()
        for index, peoples in enumerate(all):
            index = index + 1
            id = int(peoples[1])
            dbuser = self.bot.get_user(id)
            dbemail = peoples[2] if peoples[2] else "No Plex"
            dbjellyfin = peoples[3] if peoples[3] else "No Jellyfin"
            try:
                username = dbuser.name
            except:
                username = "User Not Found."
            embed.add_field(name=f"**{index}. {username}**", value=dbemail+'\n'+dbjellyfin+'\n', inline=False)

        try:
            position = int(position) - 1
            id = all[position][1]
            discord_user = await self.bot.fetch_user(id)
            username = discord_user.name
            deleted = db.delete_user(id)
            if deleted:
                print("Removed {} from db".format(username))
                await embedinfo(interaction.response,"Removed {} from db".format(username))
            else:
                await embederror(interaction.response,"Cannot remove this user from db.")
        except Exception as e:
            print(e)

async def setup(bot):
    await bot.add_cog(app(bot))
