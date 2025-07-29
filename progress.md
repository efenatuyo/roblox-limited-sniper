class for each proxy


urls: 
https://catalog.roblox.com/v1/catalog/items/details (120 items), https://apis.roblox.com/marketplace-items/v1/items/details (30 items)
both xtoken proxied 1 request/s


https://catalog.roblox.com/v1/search/items?category=All&creatorName=roblox&salesTypeFilter=2&limit=120

collectibleItemId: "de8c9733-9f5b-42a9-b9f3-b75f581e2fbd", expectedCurrency: 1, expectedPrice: 145,…}
collectibleItemId
: 
"de8c9733-9f5b-42a9-b9f3-b75f581e2fbd"
collectibleItemInstanceId
: 
"12bd63a7-7c56-41ec-883f-d4770402cb8a"
collectibleProductId
: 
"cf0385c3-3ac8-40d3-9546-c8a738eb2467"
expectedCurrency
: 
1
expectedPrice
: 
145
expectedPurchaserId
: 
"3254298971"
expectedPurchaserType
: 
"User"
expectedSellerId
: 
1
expectedSellerType
: 
null
idempotencyKey
: 
"020e39b5-0f80-4358-aff9-1e4f787fe971"


https://apis.roblox.com/marketplace-sales/v1/item/de8c9733-9f5b-42a9-b9f3-b75f581e2fbd/purchase-resale


{
    "data": [
        {
            "id": 1028606,
            "itemType": "Asset",
            "assetType": 8,
            "name": "Red Baseball Cap",
            "description": "This hat isn't worn out, it's well loved! Colored a bombastic red, with a stylish looking R that leaves no doubt which game you are playing.",
            "productId": 7834684483542479,
            "itemStatus": [],
            "itemRestrictions": [
                "Limited"
            ],
            "creatorHasVerifiedBadge": true,
            "creatorType": "User",
            "creatorTargetId": 1,
            "creatorName": "Roblox",
            "price": 7,
            "lowestPrice": 1800,
            "lowestResalePrice": 1800,
            "unitsAvailableForConsumption": 0,
            "favoriteCount": 48137,
            "offSaleDeadline": null,
            "collectibleItemId": "f9111724-5901-45f6-9b30-4ce57bd919db",
            "totalQuantity": 118943,
            "saleLocationType": "ShopOnly",
            "hasResellers": true,
            "isOffSale": true
        },
    ]

{data: [{id: 1028606, itemType: "Asset", assetType: 8, name: "Red Baseball Cap",…},…]}

{itemIds: ["8da30e50-b81b-4f61-8c6e-ce8fe7ae6500", "719940c9-5bcc-4efa-bb5e-cd240a8557a9",…]}


[
    {
        "collectibleItemId": "8da30e50-b81b-4f61-8c6e-ce8fe7ae6500",
        "name": "Epic Egg",
        "description": "This egg’s full of dozens of mini-eggs, each just as fun and creative as the last.",
        "collectibleProductId": "a643160c-9999-4aa1-809d-ea56e2c40ead",
        "itemType": 1,
        "itemRestrictions": null,
        "creatorHasVerifiedBadge": true,
        "creatorType": "User",
        "itemTargetId": 4773569689,
        "itemTargetType": 1,
        "creatorId": 1,
        "creatorName": "Roblox",
        "price": null,
        "lowestPrice": 149,
        "hasResellers": true,
        "unitsAvailableForConsumption": 0,
        "offSaleDeadline": "0001-01-01T00:00:00",
        "assetStock": 4525633,
        "errorCode": null,
        "saleLocationType": "ShopOnly",
        "universeIds": [],
        "experiences": null,
        "sales": 4525633,
        "lowestResalePrice": 149,
        "quantityLimitPerUser": 0,
        "lowestAvailableResaleProductId": "5f4182a0-6a46-4a80-96c2-d4c849aee8d9",
        "lowestAvailableResaleItemInstanceId": "4890581f-bb91-4c87-885d-fbcb461c73e8",
        "resaleRestriction": 1,
        "productSaleStatus": 0,
        "productTargetId": 3112323534207185,
        "scheduledRelease": null
    },
]

{
    "purchaseResult": "Purchase transaction success.",
    "purchased": true,
    "pending": false,
    "errorMessage": null
}


https://apis.roblox.com/marketplace-sales/v1/item/c53c885e-286f-46d0-8fac-6e28574e83e3/resellers?cursor=&limit=100

{
    "data": [
        {
            "collectibleProductId": "bd3ea0d4-1c50-4b11-8380-bbe2d87c8444",
            "collectibleItemInstanceId": "63d76b2f-21ce-4ecb-a0a3-d0c44c5b10f1",
            "seller": {
                "hasVerifiedBadge": false,
                "sellerId": 109960721,
                "sellerType": "User",
                "name": "LukyRaider"
            },
            "price": 159,
            "serialNumber": null,
            "errorMessage": null
        },
}