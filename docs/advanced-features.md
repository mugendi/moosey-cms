<!--
 Copyright (c) 2026 Anthony Mugendi

 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# Advanced Features

## `get_files`

This method is useful when inspection your content directory.

For example:

```html
{%for files in get_files('./content/guides') %} {{files}} {%endfor%}
```

The above will print out something like:

```js
{'name': 'Farming Guides', 'url': '/guides/farming', 'is_active': False, 'is_dir': True, 'order': 9999, 'group': '', 'target': '_self', 'metadata': {'title': 'Farming Guides', 'description': 'Farming guide packs with production steps, input checklists, calendars, and planning tools.', 'summary': 'Field-ready resources for farmers and agribusiness operators who want clearer planning before spending money.'}}
```

This can be useful when you want to manually build navigation links and more.

