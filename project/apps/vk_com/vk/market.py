class VkMarket:

    def __init__(self, client):
        self.client = client

    def get(self, owner_id, album_id=None, count=None,  offset=None, extended=False):
        """
        Получение списка товаров сообщества
        https://vk.com/dev/market.get

        owner_id : str
            идентификатор владельца товаров
        album_id : int
            идентификатор подборки, товары из которой нужно вернуть (по умолчанию 0)
        count : int
            количество возвращаемых товаров (по умолчанию 100)
        offset : int
            смещение относительно первого найденного товара для выборки определенного подмножества.
       
        extended : str
            1 — будут возвращены дополнительные поля likes, can_comment, can_repost, photos, views_count.
            По умолчанию: 0
        """
        action = "market.get"

        data = {'owner_id': owner_id}
        if album_id is not None:
            data['album_id'] = album_id
        if count is not None:
            data['count'] = count
        if offset is not None:
            data['offset'] = offset
        if extended is not None:
            data['extended'] = extended

        return self.client._exec_request(action, data=data)
    
    def get_by_id(self, owner_id, ids, extended=False):
        """
        Получение товара по ид
        https://vk.com/dev/market.getById

        owner_id : str
            идентификатор владельца товаров.
        ids : list:
            список ид товаров.
        extended : str
            1 — будут возвращены дополнительные поля likes, can_comment, can_repost, photos, views_count.
            По умолчанию: 0
        
        Примечание:
            item_ids - перечисленные через запятую идентификаторы
            идущие через знак подчеркивания id владельцев товаров и id самих товаров.
            Если товар принадлежит сообществу, то в качестве первого параметра используется -id сообщества.
            Пример значения item_ids "-4363_136089719,13245770_137352259"
        """
        action = "market.getById"

        item_ids = ','.join('{}_{}'.format(owner_id, item) for item in ids)
        data = {'item_ids': item_ids, 'extended': extended}
        return self.client_exec_request(action, data=data)
    
    def _get_market_upload_server(self, group_id, main_photo, crop_x=None, crop_y=None):
        action = "photos.getMarketUploadServer"
        data = {
            "group_id": group_id,
            "main_photo": 1 if main_photo else 0,
        }
        if crop_x:
            data["crop_x"] = crop_x
        if crop_y:
            data["crop_y"] = crop_y

        upload_url = self._exec_request(action, data).json()["response"]["upload_url"]
        return upload_url

    def _save_market_photo(
        self, group_id, photo, server, hash, crop_data=None, crop_hash=None
    ):
        """
        Сохранение загруженной фотографии

        crop_data, crop_hash - необязательные параметры для доп. фото
        """
        action = "photos.saveMarketPhoto"
        data = {
            "group_id": group_id,
            "photo": photo,
            "server": server,
            "hash": hash,
        }

        if crop_data:
            data["crop_data"] = crop_data
        if crop_hash:
            data["crop_hash"] = crop_hash

        resp = self._exec_request(action, data).json()
        print(resp)
        return resp["response"]

    def _upload_photo(self, url, file):
        resp = requests.post(upload_url, files={"file": file})
        return resp

    def upload_photo(self, file, group_id, main_photo, crop_x=None, crop_y=None):
        # получаем ссылку на загрузку фото
        upload_url = self._get_market_upload_server(
            group_id, main_photo, crop_x, crop_y
        )
        # загрузка фото по ссылке
        # resp = requests.post(upload_url, files={"file": file}).json()
        counter = 3
        while counter > 0:
            resp = requests.post(upload_url, files={"file": file})
            if resp.status_code == 200:
                break
            else:
                counter -= 1
                print("sleep")
                time.sleep(3 - counter)
        resp = resp.json()
        print("upload_photo", resp)
        # сохранение фото
        photo = self._save_market_photo(
            group_id,
            resp["photo"],
            resp["server"],
            resp["hash"],
            resp.get("crop_data"),
            resp.get("crop_hash"),
        )
        return photo

    def market_get_categories(self, count=200):
        """Получение категорий товаров вк"""
        action = "market.getCategories"

        data = {
            "count": count,
        }
        return self._exec_request(action, data=data)
    

    def market_get_all(self, owner_id, count=200, offset=None):
        """Получение категорий товаров вк"""
        action = "market.get"

        data = {
            "owner_id": owner_id,
            "count": count,
        }

        if offset:
            data['offset'] = offset
        return self._exec_request(action, data=data)


    def market_add(self, owner_id, name, description, category_id, **kwargs):
        action = "market.add"
        params = [
            "price",
            "old_price",
            "deleted",
            "main_photo_id",
            "photo_ids",
            "url",
            "dimension_width",
            "dimension_height",
            "dimension_length",
            "weight",
            "sku",
        ]

        for kwarg in kwargs.keys():
            if kwarg not in params:
                raise TypeError(
                    "market_add() got an unexpected keyword argument '{}'".format(kwarg)
                )
        data = {
            "owner_id": owner_id,
            "name": name,
            "description": description,
            "category_id": category_id,
        }
        data.update(kwargs)

        return self._exec_request(action, data=data)

    def market_edit(self, owner_id, item_id, **kwargs):
        action = "market.edit"
        params = [
            "name",
            "description",
            "price",
            "old_price",
            "deleted",
            "category_id",
            "photo_ids",
            "url",
            "dimension_width",
            "dimension_height",
            "dimension_length",
            "weight",
            "sku",
        ]

        for kwarg in kwargs.keys():
            if kwarg not in params:
                raise TypeError(
                    "market_edit() got an unexpected keyword argument '{}'".format(
                        kwarg
                    )
                )
        data = {
            "owner_id": owner_id,
            "item_id": item_id,
        }
        data.update(kwargs)

        return self._exec_request(action, data=data)

    def market_edit_album(self, owner_id, album_id, **kwargs):
        action = "market.editAlbum"
        params = ["title", "photo_id", "main_album"]

        for kwarg in kwargs.keys():
            if kwarg not in params:
                raise TypeError(
                    "market_edit() got an unexpected keyword argument '{}'".format(
                        kwarg
                    )
                )
        data = {
            "owner_id": owner_id,
            "album_id": album_id,
        }
        data.update(kwargs)

        return self._exec_request(action, data=data)

    def market_delete_album(self, owner_id, album_id):
        action = "market.deleteAlbum"

        data = {
            "owner_id": owner_id,
            "album_id": album_id,
        }

        return self._exec_request(action, data=data)

    def market_delete(self, owner_id, item_id):
        action = "market.delete"

        data = {
            "owner_id": owner_id,
            "item_id": item_id,
        }

        return self._exec_request(action, data=data)

    def market_album_add(self, owner_id, title, photo_id=None, main_album=0):
        """
        Добавление подборки в сообщество
        owner_id - ид владельца товара( "-" в начале если сообщество)
        """
        action = "market.addAlbum"

        data = {
            "owner_id": owner_id,
            "title": title,
            "main_album": main_album,
        }
        if photo_id:
            data["photo_id"] = photo_id

        return self._exec_request(action, data=data)

    def market_add_to_album(self, owner_id, item_id, album_ids):
        """
        Добавление товара в подборки
        owner_id - ид владельца товара( "-" в начале если сообщество)
        item_id - ид товара
        album_ids - список ид подоборок через запятую

        """
        action = "market.addToAlbum"

        data = {
            "owner_id": owner_id,
            "item_id": item_id,
            "album_ids": album_ids,
        }

        return self._exec_request(action, data=data)
    
    def market_remove_from_album(self, owner_id, item_id, album_ids):
        """
        Удаление товара из подборки
        owner_id - ид владельца товара( "-" в начале если сообщество)
        item_id - ид товара
        album_ids - список ид подоборок через запятую
        """
        action = "market.removeFromAlbum"

        data = {
            "owner_id": owner_id,
            "item_id": item_id,
            "album_ids": album_ids,
        }

        return self._exec_request(action, data=data)

    def _get_market_album_upload_server(self, group_id):
        action = "photos.getMarketAlbumUploadServer"
        data = {
            "group_id": group_id,
        }
        resp = self._exec_request(action, data).json()
        print(resp)
        upload_url = resp["response"]["upload_url"]
        return upload_url

    def _save_market_album_photo(self, data):
        """
        Сохранение загруженной фотографии подборки
        """
        action = "photos.saveMarketAlbumPhoto"

        resp = self._exec_request(action, data).json()
        print(resp)
        return resp["response"]

    def upload_album_photo(self, file, group_id):
        # получаем ссылку на загрузку фото
        upload_url = self._get_market_album_upload_server(group_id)
        # загрузка фото по ссылке
        resp = requests.post(upload_url, files={"file": file}).json()
        # сохранение фото
        resp.update({"group_id": group_id})
        photo = self._save_market_album_photo(resp)
        return photo

    # def order_items(self, user_id, order_id, offset=None, count=200):
    # закомментировано так как параметр user_id доступен только с версии 5.131, а у нас 5.124
    def order_items(self,user_id, order_id, offset=None, count=200):
        action = "market.getOrderItems"

        data = {
            "user_id": user_id,
            "order_id": order_id,
            "count": count,
        }
        if offset:
            data["offset"] = offset

        return self._exec_request(action, data=data)

    def get_order(self,user_id, order_id, extended=False):
        """
        Получение заказа по ид
        extended - расширенная информация"""
        action = "market.getOrderById"

        data = {
            "user_id": user_id,
            "order_id": order_id,
            "extended": 1 if extended else 0,
        }
        return self._exec_request(action, data=data)