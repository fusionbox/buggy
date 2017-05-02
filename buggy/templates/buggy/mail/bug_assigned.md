to: {{ assigned_to.email }}
subject: "Buggy: [{{ bug.number }}] {{ action.user.get_short_name }} assigned a bug to you. ({{ bug.project.name }})"
content-type: markdown
---
{% load absoluteuri %}# On the bug: "{{ bug.title }}" (<{{ bug.get_absolute_url|absolutize }}>)

## For project "{{ bug.project }}"

### {{ action.user.get_short_name }} {{ action.description }}
{% if action.settitle and action.order != 0 %}
### Title changed from **{{ action.settitle.previous_title }}** to **{{ action.settitle.title }}**
{% endif %}

{% if action.comment %}
{{ action.comment.comment|safe }}
{% endif %}

Get more details at <{{ bug.get_absolute_url|absolutize }}>.
