# Odoo Development Guidelines

## Environment
- Odoo Version: 19

## XML Rules
- Do NOT use `<tree>` views
- Always use `<list>` instead

## Which files cannot be changed
We can't modify anything in addons/ folder - it's standard code - we can only extend it in custom-addons/ folder. 

## Coding Standards
- Follow Odoo ORM conventions
- Use clean and modular design
- Respect Odoo Enterprise patterns
- Avoid deprecated syntax

## Behavior
- Assume all requests are for Odoo 19
- Generate production-ready code