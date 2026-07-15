"""
DATABASE STRUCTURE

Category
    │
    └──────────< Product
                     │
                     └──────────< ProductField
                                      │
                                      └──────────< ProductFieldOption


Order
    │
    └──────────< OrderItem
                     │
                     └──────────< OrderItemFieldValue
                                      │
                                      └──────────> ProductField


Relationship Legend

A ────────< B

means

One A can have many B.

Examples:

One Category
    ↓
Many Products

One Product
    ↓
Many Product Fields

One Product Field
    ↓
Many Dropdown Options

One Order
    ↓
Many Order Items

One Order Item
    ↓
Many Customer Field Values
"""