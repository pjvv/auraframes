from auraframes.api.base_api import BaseApi

from auraframes.models.activity import Activity, Comment
from auraframes.models.asset import Asset, AssetSetting
from auraframes.models.user import User


class ActivityApi(BaseApi):

    async def get_comments(self, activity_id: str) -> tuple[list[Comment], int, list[User]]:
        """
        Gets all comments on an activity.

        :param activity_id: Activity id to retrieve comments
        :return: A list of comments, the number of new (unseen)
            comments, and a list of user data associated to the comments.
        """
        json_response = await self._client.get(f'/activities/{activity_id}/comments.json')
        return (
            [Comment(**json_comment) for json_comment in json_response.get('comments', [])],
            json_response.get('new_count', 0),
            [User(**json_user) for json_user in json_response.get('users', [])]
        )

    async def create_comment(self, activity_id: str, content: str) -> tuple[Activity, Comment]:
        """
        Creates a comment on an activity.
        :param activity_id: Activity id
        :param content: The text content of the comment.
        :return: The hydrated activity and the hydrated comment.
        """
        json_response = await self._client.post(f'/activities/{activity_id}/create_comment.json', data={'content': content})

        return Activity(**json_response.get('activity', {})), Comment(**json_response.get('comment', {}))

    async def remove_comment(self, activity_id: str, comment_id: str):
        """
        Removes a comment from an activity.
        :param activity_id: Activity id
        :param comment_id: Comment id associated to the activity
        :return: The hydrated activity with the comment removed.
        """
        json_response = await self._client.post(f'/activities/{activity_id}/remove_comment.json',
                                          data={'comment_id': comment_id})

        return Activity(**json_response.get('activity', {}))

    async def get_activity_assets(self, activity_id: str, limit: int = 1000, cursor: str | None = None) -> tuple[list[Asset], list[AssetSetting]]:
        """
        Gets assets associated to an activity.

        Note: Pagination cursor may not be returned by this endpoint.

        :param activity_id: Activity id
        :param limit: Maximum number of assets per page
        :param cursor: The cursor from the previous page (if supported)
        :return: A list of assets and a list of asset settings
        """
        json_response = await self._client.get(f'/activities/{activity_id}/assets.json',
                                         query_params={'limit': limit, 'cursor': cursor})
        return (
            [Asset(**json_asset) for json_asset in json_response.get('assets', [])],
            [AssetSetting(**json_asset_setting) for json_asset_setting in json_response.get('asset_settings', [])]
        )

    async def post_activity(self, activity_id: str, frame_id: str, data: dict) -> dict:
        """
        Copy an activity to another frame.

        :param activity_id: Source activity ID
        :param frame_id: Target frame ID
        :param data: Activity data to copy
        :return: API response dict
        """
        json_response = await self._client.post(f'/activities/{activity_id}/copy.json', data=data,
                                          query_params={'frame_id': frame_id})
        return json_response

    async def delete_activity(self, activity_id: str) -> None:
        """
        Deletes an activity and its associated assets from the frame.

        :param activity_id: Activity ID to remove
        """
        await self._client.delete(f'/activities/{activity_id}')

        # Response is typically an empty JSON object.
        return None
