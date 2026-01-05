from auraframes.api.base_api import BaseApi
from auraframes.models.attachment import Attachment
from auraframes.utils.validation import validate_id, validate_caption


class AttachmentApi(BaseApi):
    """
    API for managing asset attachments (captions).

    Note: Endpoint structures are educated guesses based on observed patterns.
    May need adjustment after API testing.
    """

    async def create_caption(
        self,
        asset_id: str,
        frame_id: str,
        content: str
    ) -> Attachment:
        """
        Creates a caption on an asset.

        :param asset_id: The asset to add caption to
        :param frame_id: The frame ID (required by API)
        :param content: The caption text
        :return: The created attachment
        :raises ValidationError: If any parameter is invalid
        """
        validate_id(asset_id, "asset_id")
        validate_id(frame_id, "frame_id")
        validate_caption(content)

        data = {
            'asset_id': asset_id,
            'frame_id': frame_id,
            'type': 'caption',
            'text': content,
        }

        json_response = await self._client.post(
            '/attachments.json',
            data=data
        )
        return Attachment(**json_response.get('attachment', {}))

    async def update_caption(self, attachment_id: str, content: str) -> Attachment:
        """
        Updates an existing caption.

        :param attachment_id: The attachment ID to update
        :param content: The new caption text
        :return: The updated attachment
        """
        json_response = await self._client.put(
            f'/attachments/{attachment_id}.json',
            data={'attachment': {'content': content}}
        )
        return Attachment(**json_response.get('attachment', json_response))

    async def delete_caption(self, attachment_id: str) -> dict:
        """
        Deletes a caption/attachment.

        :param attachment_id: The attachment ID to delete
        :return: API response
        """
        return await self._client.delete(f'/attachments/{attachment_id}.json')
