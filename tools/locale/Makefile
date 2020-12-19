PYGETTEXT=pygettext3
MSGMERGE=msgmerge
MSGFMT=msgfmt

DOMAIN?=cosmonium

update-mo: *.po
	@for filename in $^; do \
	export lang=$${filename%.*} ; \
	echo "Installing $$lang for $(DOMAIN)" ; \
	mkdir -p ../locale/$$lang/LC_MESSAGES ; \
	$(MSGFMT) $$filename -o ../locale/$$lang/LC_MESSAGES/$(DOMAIN).mo ; \
	done

update-pot:
	@$(PYGETTEXT) -d $(DOMAIN) ../cosmonium ../main.py

update-po: *.po

%.po: $(DOMAIN).pot
	@echo "Update $@ for $(DOMAIN)"
	@$(MSGMERGE) -U $@ $(DOMAIN).pot

.PHONY: update-mo update-po update-pot
