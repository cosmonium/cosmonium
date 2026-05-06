{{ fullname | escape | underline }}

.. automodule:: {{ fullname }}
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

{% block modules %}
{%- if modules %}
.. rubric:: Submodules

.. autosummary::
   :toctree:
   :recursive:
   :nosignatures:

{% for item in modules %}
   {{ fullname }}.{{ item }}
{%- endfor %}
{%- endif %}
{%- endblock %}
