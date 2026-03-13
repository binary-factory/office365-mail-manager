📧 **E-Mail Report** — {{timestamp}}

Habe {{total_count}} E-Mails verarbeitet:

{{#categories}}
## {{category_name}} ({{count}})

{{#mails}}
**{{index}}. {{subject}}**
   - Von: {{sender}}
   - Zeit: {{received_time}}
   - **Aktion:** {{action_taken}}
   - **Begründung:** {{reasoning}}

{{/mails}}

{{/categories}}

{{#uncertain_count}}
⚠️ **Unsicher bei {{uncertain_count}} E-Mails** — Bitte Feedback:
{{#uncertain_mails}}
- **{{index}}:** {{subject}}
  → Ich habe als "{{my_decision}}" markiert. Stimmt das?
{{/uncertain_mails}}
{{/uncertain_count}}

---

💬 **Dein Feedback?**

Antworte mit:
- `"Alles gut"` — Alles korrekt
- `"{{index}} falsch, {{correction}}"` — z.B. "3 falsch, wichtig"
- `"Absender@firma.de immer {{category}}"` — Lerne Muster
- `"{{keyword}} immer {{action}}"` — Neue Regel

**Aktionen zusammengefasst:**
- {{stats.important}} als wichtig markiert
- {{stats.newsletter}} als Newsletter archiviert
- {{stats.invoice}} Rechnungen weitergeleitet
- {{stats.read}} als gelesen markiert

{{#learned_rules_applied}}
📚 **Angewandte Regeln:**
{{#rules}}
- {{description}}
{{/rules}}
{{/learned_rules_applied}}
