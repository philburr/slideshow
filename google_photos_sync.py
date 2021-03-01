import sys
from os.path import join, dirname, isfile, abspath
from os import listdir, remove
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseDownload
from collections import namedtuple
import requests

class GooglePhotos(object):
    SCOPES = 'https://www.googleapis.com/auth/photoslibrary.readonly'
    ALBUM_NAME = 'Missionary Board'

    def __init__(self, root):
        self.photos_dir = abspath(root)
        self.store = file.Storage(join(dirname(__file__), 'token-for-google.json'))
        self.creds = self.store.get()
        if not self.creds or self.creds.invalid:
            self.flow = client.flow_from_clientsecrets(join(dirname(__file__), 'client_secret.json'), scope=self.SCOPES, redirect_uri='http://localhost:8080/')
            self.creds = tools.run_flow(self.flow, self.store)
        self.http=self.creds.authorize(Http())
        self.google_photos = build('photoslibrary', 'v1', self.http)

    def sync(self):
        albums = self.google_photos.albums().list(pageSize=10).execute()
        albums = albums.get('albums', [])
        changed = False
        for album in albums:
            name = album['title']
            if name == self.ALBUM_NAME:
                changed = changed or self.sync_album(album['id'])

        return changed


    def sync_album(self, id):
        album_filter = [{"albumId": "id"}]
        nextpagetoken = 'Dummy'

        all_photos = []
        while nextpagetoken != '':
            nextpagetoken = '' if nextpagetoken == 'Dummy' else nextpagetoken
            results = self.google_photos.mediaItems().search(body={"albumId": id, "pageSize": 10, "pageToken": nextpagetoken}).execute()
            items = results.get('mediaItems', [])
            nextpagetoken = results.get('nextPageToken', '')
            for item in items:
                all_photos.append((item['filename'], item['baseUrl'], item['id']))

        all_filenames = [name for name,_,_ in all_photos]
        cached_filenames = []

        # remove files not in the album anymore
        changed = False
        for name in listdir(self.photos_dir):
            if isfile(join(self.photos_dir, name)) and not name in all_filenames:
                remove(join(self.photos_dir, name))
                changed = True
            else:
                cached_filenames.append(name)

        # remove cached_filenames from all_photos
        all_photos = [(name, url, id) for name, url, id in all_photos if not name in cached_filenames]
        changed = changed or (len(all_photos) > 0)

        # download files in the album, not local
        for name, url, id in all_photos:
            url = url + "=d"
            req_data = {'uri': url, 'http': self.http, 'headers': {}}
            req = namedtuple("Request", req_data.keys())(*req_data.values())

            with open(join(self.photos_dir, name), 'wb') as f:
                downloader = MediaIoBaseDownload(f, req)
                done = False
                while done is False:
                    _, done = downloader.next_chunk()

        return changed

if __name__ == '__main__':
    gp = GooglePhotos('photos/')
    gp.sync()
