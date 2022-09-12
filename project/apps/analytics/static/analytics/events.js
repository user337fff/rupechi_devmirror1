/**
 * Подробнее https://netpeak.net/ru/blog/kak-nastroit-rasshirennuyu-elektronnuyu-torgovlyu-s-pomoshch-yu-google-tag-manager/
 */

window.dataLayer = window.dataLayer || [];


// 1. Просмотры товаров в каталоге
function impressions(products) {
    let data = {
        ecommerce: {
          currencyCode: "RUB",
          impressions: [],
        },
        event: "gtm-ee-event",
        "gtm-ee-event-category": "Enhanced Ecommerce",
        "gtm-ee-event-action": "Product Impressions",
        "gtm-ee-event-non-interaction": "True",
      }

    products.forEach(function(item, i) {
        product = {
            name: item.title,
            id: item.id,
            price: item.price,
            brand: item.brand,
            category: item.category,
            position: i,
        }
        data.ecommerce.impressions.push(product)
    });

    dataLayer.push(data)
}

// 2. Клики по товарам
// не предусмотрено

// 3. Просмотры карточек товаров
function detail(product) {
    let data = {
        ecommerce: {
          currencyCode: "RUB",
          detail: {
                    name: product.title,
                    id: product.id,
                    price: product.price,
                    brand: product.brand,
                    category: product.category,
                 },
        },
        event: "gtm-ee-event",
        "gtm-ee-event-category": "Enhanced Ecommerce",
        "gtm-ee-event-action": "Product Details",
        "gtm-ee-event-non-interaction": "True",
      }

    dataLayer.push(data)
}


// 4. Добавление товара в корзину

function add(product) {
    let data = {
        ecommerce: {
          currencyCode: "RUB",
          add: {
            products: [
              {
                name: product.title,
                id: product.id,
                price: product.price,
                brand: product.brand,
                category: product.category,
              },
            ],
          },
        },
        event: "gtm-ee-event",
        "gtm-ee-event-category": "Enhanced Ecommerce",
        "gtm-ee-event-action": "Adding a Product to a Shopping Cart",
        "gtm-ee-event-non-interaction": "False",
      }

    dataLayer.push(data)
}

// 5. Удаление товара из корзины
function remove(product) {
    let data = {
        ecommerce: {
          currencyCode: "RUB",
          remove: {
            products: [
              {
                name: product.title,
                id: product.id,
                price: product.price,
                brand: product.brand,
                category: product.category,
              },
            ],
          },
        },
        event: "gtm-ee-event",
        "gtm-ee-event-category": "Enhanced Ecommerce",
        "gtm-ee-event-action": "Removing a Product from a Shopping Cart",
        "gtm-ee-event-non-interaction": "False",
      }

    dataLayer.push(data)
}



// // 6. Шаги оформления заказа

// // На каждом шаге меняем  actionField: { step: 1 },
// // и  "gtm-ee-event-action": "Checkout Step 3",
// // Шаг 1. Переход в корзину.
// // Шаг 2. Ввод контактных данных.
// // Шаг 3. Ввод способа доставки.
// // Шаг 4. Ввод способа оплаты.
// // Шаг 5. Подтверждение заказа.
// // Шаг 6. Thank You Page.

// dataLayer.push({
//   ecommerce: {
//     currencyCode: "RUB",
//     checkout: {
//       actionField: { step: 1 },
//       products: [
//         {
//           name: "Product 1",
//           id: "ID1",
//           price: "23.5",
//           brand: "Brand 1",
//           category: "Category 1/Subcategory 11",
//           variant: "Variant 1",
//           quantity: 2,
//         },
//       ],
//     },
//   },
//   event: "gtm-ee-event",
//   "gtm-ee-event-category": "Enhanced Ecommerce",
//   "gtm-ee-event-action": "Checkout Step 1",
//   "gtm-ee-event-non-interaction": "False",
// });


// // 7. Варианты оформления заказа

// dataLayer.push({
//   ecommerce: {
//     currencyCode: "RUB",
//     checkout: {
//       actionField: { step: 3, option: "Новая почта" },
//       products: [
//         {
//           name: "Product 1",
//           id: "ID1",
//           price: "23.5",
//           brand: "Brand 1",
//           category: "Category 1/Subcategory 11",
//           variant: "Variant 1",
//           quantity: 2,
//         },
//       ],
//     },
//   },
//   event: "gtm-ee-event",
//   "gtm-ee-event-category": "Enhanced Ecommerce",
//   "gtm-ee-event-action": "Checkout Step 3",
//   "gtm-ee-event-non-interaction": "False",
// });

// dataLayer.push({
//   ecommerce: {
//     currencyCode: "RUB",
//     checkout: {
//       actionField: { step: 4, option: "Банковская карта" },
//       products: [
//         {
//           name: "Product 1",
//           id: "ID1",
//           price: "23.5",
//           brand: "Brand 1",
//           category: "Category 1/Subcategory 11",
//           variant: "Variant 1",
//           quantity: 2,
//         },
//       ],
//     },
//   },
//   event: "gtm-ee-event",
//   "gtm-ee-event-category": "Enhanced Ecommerce",
//   "gtm-ee-event-action": "Checkout Step 4",
//   "gtm-ee-event-non-interaction": "False",
// });


// // 8. Совершенные покупки
// dataLayer.push({
//   ecommerce: {
//     currencyCode: "RUB",
//     purchase: {
//       actionField: {
//         id: "TID1",
//         affiliation: "Online Store",
//         revenue: "91.4",
//         tax: "9.4",
//         shipping: "35",
//         coupon: "Coupon 1",
//       },
//       products: [
//         {
//           name: "Product 1",
//           id: "ID1",
//           price: "23.5",
//           brand: "Brand 1",
//           category: "Category 1/Subcategory 11",
//           variant: "Variant 1",
//           quantity: 2,
//           coupon: "",
//         },
//       ],
//     },
//   },
//   event: "gtm-ee-event",
//   "gtm-ee-event-category": "Enhanced Ecommerce",
//   "gtm-ee-event-action": "Purchase",
//   "gtm-ee-event-non-interaction": "False",
// });
