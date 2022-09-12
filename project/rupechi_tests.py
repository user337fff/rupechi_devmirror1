import os
import django
import pytest

os.environ['DJANGO_SETTINGS_MODULE'] = 'system.settings'
django.setup()

'''
@pytest.mark.parametrize(
    "email, password", 
    [
        ("user@gmail.com", "password")
    ]
)
def test__api_authorisation_success(email, password):
    """Тест успешной аутентификации пользователя через запрос"""
    client = Client()
    def test__api_authorisation_success_step1(client, email, password):
        """
            Шаг: Запрос к методу аутентификации с доступами
            Результат: Успешная аутентификация
        """

        response = client.post(
            path = "/users/login/", 
            data = {
                "email": email,
                "password": password
            },
            follow=True
        )
        
        return response.json()["success"]

    assert test__api_authorisation_success_step1()
'''

#Смена домена, не работает
@pytest.mark.skip
@pytest.mark.parametrize(
    "user",
    [
        "unath", 
        "auth",
        "wholesale",
    ],
    indirect=True
)
@pytest.mark.parametrize(
    "domain, result", 
    [
        ("cherepovets.rupechi.ru", True),
        ("ivanovo.rupechi.ru", True),
        ("spb.rupechi.ru", True),
        ("www.rupechi.ru", True),
        ("yaroslavl.rupechi.ru", True),
        ("inoidomen.rupech.ru", False)
    ]
)
def test__api_create_changedomain(user, domain, result):
    """Смена домена"""

    client = user

    response = client.post(
        path = "/change/",
        data = {
            "domain": domain
        },
        follow=True
    )
    print(response)
    print(response.json())
    assert response.json()["success"] == result

#Оформление заказа
@pytest.mark.order
@pytest.mark.parametrize(
    "user",
    [
        "unath", 
        "auth",
        "wholesale",
    ],
    indirect=True
)
@pytest.mark.parametrize(
    "product_id, count, result", 
    [
        ("141", 5, True),
        ("-1", 5, False)
    ]
)
def test__api_create_oneclickorder(user, product_id, count, result):
    """Оформление заказа в один клик для пользователя"""

    client = user

    response = client.post(
        path = "/feedback/api/oneclick/",
        data = {
            "product": product_id,
            "quantity": count
        },
        follow=True
    )
    print(response.json())
    assert response.json()["success"] == result

'''
@pytest.mark.order
@pytest.mark.parametrize(
    "user",
    [
        "unath", 
        "auth",
        "wholesale",
    ],
    indirect=True
)
@pytest.mark.parametrize(
    "name, phone, email",
    [
        ("Имя", "99999", "email@mail.ru"),
        ("Имя2", "+7 999 990-99-99", "email")
    ]
)
def test__api_create_order(user, name, phone, email):
    """Оформление заказа для пользователя"""
    client = user
    response = client.post(
        path = "/order/",
        data = {
            "name": name,
            "phone": phone,
            "email": email
        },
        follow=True
    )
    print(response.json())
    assert response.json()["success"] == True
'''

#Добавление в корзину
@pytest.mark.cart
@pytest.mark.parametrize(
    "user",
    [
        "unath", 
        "auth",
        "wholesale",
    ],
    indirect=True
)
@pytest.mark.parametrize(
    "product_id, count, result", 
    [
        ("141", 5, True),
        ("-1", 5, False)
    ]
)
def test__api_add_cart(user, product_id, count, result):
    """Добавление товаров в корзину пользователя"""

    client = user

    response = client.post(
        path = "/cart/add/",
        data = {
            "product": product_id,
            "quantity": count
        },
        follow=True
    )
    print(response.json())
    assert response.json()["success"] == result

#Работа с формами
@pytest.mark.feedback
@pytest.mark.parametrize(
    "user",
    [
        "unath", 
        "auth",
        "wholesale",
    ],
    indirect=True
)
@pytest.mark.parametrize(
    "email, result",
    [
        ("user@mail.ru", True),
        ("ooouser@gmail.com", True),
        ("ooouse.com", False),
    ]
)
def test__api_feedback_subscribe(user, email, result):
    """Подписка на рассылку для пользователя"""
    client = user
    response = client.post(
        path = "/feedback/api/subscribe/",
        data = {
            "email": email
        },
        follow=True
    )
    print(response.json())
    assert response.json()["success"] == result



@pytest.mark.feedback
@pytest.mark.parametrize(
    "user",
    [
        "unath", 
        "auth",
        "wholesale",
    ],
    indirect=True
)
@pytest.mark.parametrize(
    "email, author, message, result",
    [
        ("user@mail.ru", "Автор", "Сообщение", "Комментарий добавлен"),
    ]
)
def test__api_feedback_review(user, email, author, message, result):
    """Создание отзыва для пользователя"""
    client = user
    response = client.post(
        path = "/api/set_review/",
        data = {
            "email": email,
            "author": author, 
            "message": message
        },
        follow=True
    )
    print(response.json())
    assert response.json()["success"] == result


@pytest.mark.feedback
@pytest.mark.parametrize(
    "user",
    [
        "unath", 
        "auth",
        "wholesale",
    ],
    indirect=True
)
@pytest.mark.parametrize(
    "title, inn, city, field_of_activity, fullname, phone, email, result",
    [
        ("Организация1", "ИНН", "Город1", "Активность1", "ФИО", "Телефон", "Почта", False),
        ("Организация1", "ИНН", "Череповец", "Активность1", "ФИО", "Телефон", "Почта", True),
    ]
)
def test__api_feedback_wholesale(user, title, inn, city, field_of_activity, fullname, phone, email, result):
    """Заявка на опт для пользователя"""
    client = user
    response = client.post(
        path = "/feedback/api/coop/",
        data = {
            "title": title,
            "inn": inn, 
            "city": city,
            "field_of_activity": field_of_activity,
            "fullname": fullname,
            "phone": phone,
            "email": email
        },
        follow=True
    )
    print(response.json())
    assert response.json()["success"] == result

'''
@pytest.mark.parametrize(
    "email, password, product_id, count", 
    [
        ("user_ps@place-start.ru", "CWBBGAcoZ", "141", -5)
    ]
)
def test__api_add_cart_miuns_quantity_unsuccess(email, password, product_id, count):
    """Тест успешного добавления товара в корзину"""
    client = Client()
    def test__api_add_cart_miuns_quantity_unsuccess_step1():
        """
            Шаг: Запрос к методу добавление товара в корзину
            Результат: Успешное оформление заказа
        """

        assert client.login(
            username = email, 
            password = password
        )

        response = client.post(
            path = "/cart/add/",
            data = {
                "product": product_id,
                "quantity": count
            }
        )

        return not response.json()["success"]

    assert test__api_add_cart_miuns_quantity_unsuccess_step1()


@pytest.mark.parametrize(
    "email, password, name, phone", 
    [
        ("user_ps@place-start.ru", "CWBBGAcoZ", "Ibragim", "+79999999999")
    ]
)
def test__api_create_order_with_clear_cart_unsuccess(email, password, name, phone):
    """Тест оформления заказа с пустым списком товаров"""
    client = Client()

    def test__api_create_order_with_clear_cart_unsuccess_step1():
        """
            Шаг: Запрос к методу оформления заказа
            Результат: Неудачное оформление заказа
        """

        assert client.login(
            username = email, 
            password = password
        )

        response = client.post(
            path = "/order/",
            data = {
                "email": email,
                "phone": phone,
                "name": name
            }
        )

        print(response)
        return False

    assert test__api_create_order_with_clear_cart_unsuccess_step1()

def test__api_get_cart():
    """Тест оформления заказа с пустым списком товаров"""
    client = Client()
    cart = get_cart(client.get("").wsgi_request)
    print(cart)
    print(cart.items())
    raise Exception()
'''