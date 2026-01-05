from auraframes.api.base_api import BaseApi


class PlaylistApi(BaseApi):

    async def get_playlist_asset_ids(self, playlist_id: str, frame_id: str, _filter: str | None = None, limit: int = 1000,
                            cursor: str | None = None) -> tuple[list[str], str | None]:
        """
        Gets asset IDs for a playlist/album.

        :param playlist_id: Playlist/album ID
        :param frame_id: Frame ID the playlist belongs to
        :param _filter: Optional filter
        :param limit: Maximum assets per page (default 1000)
        :param cursor: Pagination cursor
        :return: List of asset IDs and next page cursor
        """
        json_response = await self._client.get(f'/playlists/{playlist_id}/assets.json',
                         query_params={'frame_id': frame_id, 'filter': _filter, 'limit': limit, 'cursor': cursor})
        # The endpoint returns asset_settings, not full assets
        asset_ids = [setting['asset_id'] for setting in json_response.get('asset_settings', [])]
        return asset_ids, json_response.get('next_page_cursor')
