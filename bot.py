from botbuilder.core import TurnContext
from botbuilder.core.teams import TeamsActivityHandler
from botbuilder.schema import ChannelAccount
from botbuilder.schema.teams import TeamInfo, TeamsChannelAccount
from botframework.connector.auth import List


class TeamsStartThreadInChannel(TeamsActivityHandler):
    def __init__(self, app_id: str):
        self._app_id = app_id

    async def on_teams_members_added(  # pylint: disable=unused-argument
        self,
        teams_members_added: [TeamsChannelAccount],
        team_info: TeamInfo,
        turn_context: TurnContext,
    ):
        print('on_teams_members_added')


    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        print('on_members_added_activity')



    async def on_message_activity(self, turn_context: TurnContext):
        print('on_message_activity')
