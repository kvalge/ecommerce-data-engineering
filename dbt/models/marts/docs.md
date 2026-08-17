{% docs mart_sales %}
Sales performance mart: revenue and volume aggregated by order date, shipping city, and order status. Built from `fct_order_items` for reporting dashboards.
{% enddocs %}

{% docs mart_customers %}
Customer behavior mart: one row per current user with order counts, first/last order dates, and lifetime revenue/units. Combines `dim_users` with order and line facts.
{% enddocs %}

{% docs mart_products %}
Product performance mart: one row per catalog product with units sold, revenue, and order coverage. Combines `dim_products` with `fct_order_items`.
{% enddocs %}

{% docs ecommerce_overview %}
E-commerce analytics dbt project.

Layers:
- **staging** — cleaned views over `raw.*`
- **intermediate** — star-schema dims and facts (including SCD2 as-of user attributes on orders)
- **marts** — analytical aggregates for sales, customers, and products
{% enddocs %}
