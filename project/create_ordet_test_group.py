import pytest

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
    "product_id, count", 
    [
        ("141", 5)
    ]
)
def test__api_add_cart(user, product_id, count):
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
    assert response.json()["success"] == True


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
    print(user, name, phone, email)
    print(response)
    print(response.json())
    assert response.json()["success"] == True