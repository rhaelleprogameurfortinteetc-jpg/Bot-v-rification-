import aiohttp 
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

FORTNITE_API_KEY = "4e63b859-865a-4fb8-bec9-90f2504dce4c"
# --- 1. Requête vers Fortnite-API.com ---
async def get_fortnite_stats(username: str):
    url = f"https://fortnite-api.com/v1/stats/br/v2?name={username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                json_data = await resp.json()
                return json_data.get("data")
            return None

# --- 2. Le Tiroir (Menu déroulant) pour les stats ---
class StatsSelect(discord.ui.Select):
    def __init__(self, stats_data):
        self.stats = stats_data
        options = [
            discord.SelectOption(label="Globales", description="Stats globales Battle Royale", emoji="🏆"),
            discord.SelectOption(label="Solo", description="Stats en mode Solo", emoji="👤"),
            discord.SelectOption(label="Duo", description="Stats en mode Duo", emoji="👥"),
            discord.SelectOption(label="Squad", description="Stats en mode Section", emoji="👨‍👩‍👧‍👦")
        ]
        super().__init__(placeholder="Choisis le mode pour voir tes stats...", options=options)

    async def callback(self, interaction: discord.Interaction):
        mode = self.values[0]
        name = self.stats["account"]["name"]
        all_stats = self.stats["stats"]["all"]

        if mode == "Globales":
            selected = all_stats.get("overall", {})
        elif mode == "Solo":
            selected = all_stats.get("solo", {})
        elif mode == "Duo":
            selected = all_stats.get("duo", {})
        else:
            selected = all_stats.get("squad", {})

        if not selected:
            await interaction.response.send_message(f"Aucune statistique trouvée pour le mode {mode}.", ephemeral=True)
            return

        wins = selected.get("top1", 0)
        kills = selected.get("kills", 0)
        kd = selected.get("kd", 0)
        matches = selected.get("matches", 0)

        embed = discord.Embed(title=f"📊 Stats {mode} — {name}", color=discord.Color.green())
        embed.add_field(name="Top 1 🏆", value=str(wins), inline=True)
        embed.add_field(name="Kills ⚔️", value=str(kills), inline=True)
        embed.add_field(name="K/D 🎯", value=str(kd), inline=True)
        embed.add_field(name="Parties 🎮", value=str(matches), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

class StatsView(discord.ui.View):
    def __init__(self, stats_data):
        super().__init__()
        self.add_item(StatsSelect(stats_data))

# --- 3. Commande /lier avec le message explicatif ---
@tree.command(name="lier", description="Lie ton compte Epic Games et affiche tes stats")
async def lier(interaction: discord.Interaction, pseudo_epic: str):
    await interaction.response.defer(ephemeral=True)

    data = await get_fortnite_stats(pseudo_epic)

    # Si le compte n'existe pas ou que les stats sont privées
    if not data:
        embed_erreur = discord.Embed(
            title="❌ Impossible de vérifier ton compte",
            description=(
                f"Le pseudo **{pseudo_epic}** est introuvable ou tes statistiques sont privées.\n\n"
                "**Comment rendre tes stats publiques sur Fortnite :**\n"
                "1. Ouvre **Fortnite** ➔ **Paramètres ⚙️**\n"
                "2. Va dans l'onglet **Compte et confidentialité 👤**\n"
                "3. Dans **Confidentialité du jeu**, active **Afficher sur le classement de la carrière** sur **OUI**.\n"
                "4. Relance la commande `/lier` !"
            ),
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed_erreur, ephemeral=True)
        return

    # Attribution automatique du rôle 'Vérifié'
    role = discord.utils.get(interaction.guild.roles, name="Vérifié")
    if role:
        await interaction.user.add_roles(role)

    # Message de succès avec le tiroir de stats
    embed_succes = discord.Embed(
        title="✅ Compte Epic Games vérifié !",
        description=(
            f"Bienvenue **{data['account']['name']}** ! Ton compte est lié.\n\n"
            "• Le rôle **Vérifié** t'a été attribué.\n"
            "• Utilise le menu déroulant (tiroir) ci-dessous pour consulter tes statistiques par mode !"
        ),
        color=discord.Color.blue()
    )

    view = StatsView(data)
    await interaction.followup.send(embed=embed_succes, view=view, ephemeral=True)
