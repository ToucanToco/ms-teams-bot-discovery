from datetime import datetime
from http import HTTPStatus
import sys
import traceback
import uuid

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (BotFrameworkAdapter, BotFrameworkAdapterSettings, CardFactory, MessageFactory, TurnContext)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes, ConversationParameters
from botframework.connector import ConnectorClient
from botframework.connector.auth import MicrosoftAppCredentials
from botframework.connector.teams import TeamsConnectorClient

from bot import TeamsStartThreadInChannel
from config import DefaultConfig

CONFIG = DefaultConfig()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error

# If the channel is the Emulator, and authentication is not in use, the AppId will be null.
# We generate a random AppId for this case only. This is not required for production, since
# the AppId will have a value.
APP_ID = SETTINGS.app_id if SETTINGS.app_id else uuid.uuid4()

# Create the Bot
BOT = TeamsStartThreadInChannel(CONFIG.APP_ID)


# Listen for incoming requests on /api/messages.
async def messages(req: Request) -> Response:
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)


async def send_message(req: Request) -> Response:
    try:
        credentials = MicrosoftAppCredentials(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
        client = ConnectorClient(credentials, 'https://smba.trafficmanager.net/fr/')
        teams_client = TeamsConnectorClient(credentials, 'https://smba.trafficmanager.net/fr/')
        teams_channels = teams_client.teams.get_teams_channels('19:96de6561548648858071872e920a028e@thread.tacv2')
        for teams_channel in teams_channels.conversations:
            conversation_parameters = ConversationParameters(
                is_group=True,
                channel_data={"channel": {"id": teams_channel.id}},
                activity=MessageFactory.content_url('https://picsum.photos/200/300', 'image/png'),
            )
            client.conversations.create_conversation(conversation_parameters)
        return Response(status=HTTPStatus.OK)
    except Exception:
        traceback.print_exc()


async def send_execsum(req: Request) -> Response:
    try:
        credentials = MicrosoftAppCredentials(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
        client = ConnectorClient(credentials, 'https://smba.trafficmanager.net/fr/')
        teams_client = TeamsConnectorClient(credentials, 'https://smba.trafficmanager.net/fr/')
        teams_channels = teams_client.teams.get_teams_channels('19:96de6561548648858071872e920a028e@thread.tacv2')
        for teams_channel in teams_channels.conversations:
            conversation_parameters = ConversationParameters(
                is_group=True,
                channel_data={"channel": {"id": teams_channel.id}},
                activity=MessageFactory.attachment(
                    CardFactory.adaptive_card({
                        "type": "AdaptiveCard",
                        "version": "1.0",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "william.gorge@toucantoco.com sent an execsum",
                            },
                        ],
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "View execsum",
                                "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
                            }
                        ]
                    })
                ),
            )
            client.conversations.create_conversation(conversation_parameters)
        return Response(status=HTTPStatus.OK)
    except Exception:
        traceback.print_exc()

APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

APP.router.add_post("/api/messages/send", send_message)
APP.router.add_post("/api/messages/send-execsum", send_message)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error

# TODO check how to get the serviceURL: we get it when the bot is added. Anyway it does not seem to change https://docs.microsoft.com/fr-fr/microsoftteams/platform/resources/bot-v3/bots-context (source: "The value of serviceUrl tends to be stable but can change. When a new message arrives, your bot should verify its stored value of serviceUrl.")

# Problème conversations
# TODO si envoi seulement de laputa vers ms teams => bcp moins complexe (pas besoin de gêrer des messages)
# TODO ok d'envoyer un lien vers l'execsum? compliqué d'uploader un fichier PDF vers teams, besoin de gêrer une conversation
# TODO si on veut avoir synchro commentaires stories dans MS Teams; là c'est obligé d'avoir un service de bot

# Problème one bot to rule them all (dans le cas où on a besoin d'un bot)
# TODO check with margot if we can have the client create and install an app manually
# TODO cout d'un service de base