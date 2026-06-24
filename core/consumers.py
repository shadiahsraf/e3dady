import json
from channels.generic.websocket import AsyncWebsocketConsumer


class LiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('live', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('live', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def scan_event(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def team_complete(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def session_event(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def leaderboard_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
