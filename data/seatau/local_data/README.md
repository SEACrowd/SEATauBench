# Localization seed and template reference

This directory is a design artifact, not runtime code.

It shows how locale-specific synthetic data can be split into two layers:

- seed lists: atomic names, place names, and address parts
- templates: the patterns used to combine those seeds into realistic values

The current runtime still uses Faker-based generation. These files are here
so you can inspect the shape of a larger corpus before wiring it into code.

## Layout

```text
local_data/
├── seeds/
│   ├── id.json
│   ├── th.json
│   ├── tl.json
│   ├── vi.json
│   └── zh.json
└── templates/
    ├── id.json
    ├── th.json
    ├── tl.json
    ├── vi.json
    └── zh.json
```

## What goes in the seed lists

Keep the seed lists atomic. A good split is:

- person: given names, family names, honorifics, name particles
- address: street names, street prefixes, subdistricts, districts, cities,
  provinces, postal codes

This keeps the corpus composable. You can grow the lists independently
without rewriting templates.

## What goes in the templates

Templates should reflect local formatting rules, not just vocabulary.

Examples:

- Vietnamese: `Nguyễn Minh Anh`, `Số 12 Đường Lê Lợi, Quận 1, TP. Hồ Chí Minh`
- Chinese: `王子涵`, `北京市海淀区中山路12号`
- Filipino: `Ms. Patricia Cruz`, `Blk 4 Lot 12, Rizal St., Quezon City`

## How to scale this

The cleanest scaling path is:

1. Start with a small, hand-curated seed set for smoke tests.
2. Split seeds into `common`, `regional`, and `rare` buckets when the
   lists get large.
3. Add template variants for each locale instead of forcing one global
   address format.
4. Introduce weights later if you need sampling control.
5. Keep placeholders stable so the same corpus can feed multiple generators.

For a larger production corpus, the next step would be to break each locale
into slot-specific files, for example:

- `person/given_names.json`
- `person/family_names.json`
- `address/cities.json`
- `address/templates.json`

That lets you scale each slot separately without creating one giant file.
